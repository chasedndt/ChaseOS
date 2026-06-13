"""Digest-gated personal context import preview writer.

This surface converts operator-provided personal context text into a bounded
review packet for a future import execution pass. It can queue one approval
request through ``StudioService`` after the operator supplies the exact preview
digest, but it never writes raw context, markdown nodes, indexes, Personal Map
candidates, runtime memory, or canonical project/knowledge state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.personal_context_import import (
    CANONICAL_KNOWLEDGE_INDEX_PATH,
    PERSONAL_MAP_CANDIDATE_DIR,
    RAW_INTAKE_DIR,
    ROOT_KNOWLEDGE_SHIM_PATH,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.personal_context_import_preview_writer.v1"
SURFACE_ID = "studio_personal_context_import_preview_writer"
PASS_ID = "personal-context-import-approved-preview-writer"
STATUS_PREVIEW = "READY / APPROVAL-QUEUE-WRITE-PREVIEW / CONTEXT IMPORT WRITES BLOCKED"
STATUS_WRITTEN = "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / CONTEXT IMPORT WRITES BLOCKED"
BLOCKED_STATUS = "BLOCKED / APPROVAL-PREVIEW / NO APPROVAL ARTIFACT WRITE"
NEXT_RECOMMENDED_PASS = "personal-context-import-approved-preview-execution-proof"
APPROVAL_CLASS = "personal_context_import_preview_future"
PREVIEW_ROOT = "runtime/studio/context-import/previews"
AUDIT_ROOT = "runtime/studio/approvals/personal-context-import"
SECRET_TOKEN = "[REDACTED_SECRET]"

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai_style_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE)),
    ("github_token", re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b", re.IGNORECASE)),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{16,}\b", re.IGNORECASE)),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    (
        "token_assignment",
        re.compile(r"(?i)\b(?:api[_ -]?key|secret|token|credential|password)\s*[:=]\s*[^\s,;]{8,}"),
    ),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("seed_phrase", re.compile(r"(?i)\b(?:seed phrase|recovery phrase|wallet seed|private key|wallet key)\b")),
    ("webhook_url", re.compile(r"https://(?:discord(?:app)?\.com/api/webhooks|hooks\.slack\.com/services)/[^\s]+", re.IGNORECASE)),
)

SOURCE_TEXT_MAX_CHARS = 240_000


NODE_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "identity_doctrine",
        "label": "Identity / Doctrine / Discipline",
        "family": "identity_doctrine",
        "parent_path": "SOUL.md",
        "target_path": "SOUL.md",
        "target_kind": "protected_identity_route",
        "keywords": ("soul", "identity", "doctrine", "discipline", "principles", "values", "decision rules", "no zero days"),
        "index_targets": ("00_HOME/Personal-Operator-Index.md", "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md"),
    },
    {
        "id": "fitness_combat_physical_discipline",
        "label": "Fitness / Combat / Physical Discipline",
        "family": "personal_domains",
        "parent_path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "target_path": "00_HOME/Personal-Domains/Fitness-Combat-Physical-Discipline.md",
        "target_kind": "personal_domain_node",
        "keywords": ("fitness", "combat", "gym", "boxing", "running", "recovery", "physical discipline", "training"),
        "index_targets": ("02_KNOWLEDGE/Fitness/Fitness-Physical.md",),
    },
    {
        "id": "interests_knowledge_domains",
        "label": "Interests / Knowledge Domains",
        "family": "personal_domains",
        "parent_path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "target_path": "00_HOME/Personal-Domains/Interests-Knowledge-Domains.md",
        "target_kind": "personal_domain_node",
        "keywords": ("interests", "hobbies", "piano", "geopolitics", "history", "youtube monetization", "content creation"),
        "index_targets": ("02_KNOWLEDGE/Platform-Strategy/Platform-Strategy.md", "02_KNOWLEDGE/Content-Distribution/Content-Distribution.md"),
    },
    {
        "id": "piano_interest",
        "label": "Piano",
        "family": "personal_interests",
        "parent_path": "00_HOME/Personal-Domains/Interests-Knowledge-Domains.md",
        "target_path": "00_HOME/Personal-Domains/Interests-Knowledge-Domains.md#piano",
        "target_kind": "interest_child_node",
        "keywords": ("piano",),
        "index_targets": ("00_HOME/Personal-Domains/Personal-Domains-Index.md",),
    },
    {
        "id": "geopolitics_history_interest",
        "label": "Geopolitics / History",
        "family": "personal_interests",
        "parent_path": "00_HOME/Personal-Domains/Interests-Knowledge-Domains.md",
        "target_path": "00_HOME/Personal-Domains/Interests-Knowledge-Domains.md#geopolitics-history",
        "target_kind": "interest_child_node",
        "keywords": ("geopolitics", "geo politics", "history"),
        "index_targets": ("02_KNOWLEDGE/Platform-Strategy/Platform-Strategy.md",),
    },
    {
        "id": "language_learning_global_mobility",
        "label": "Language Learning / Global Mobility",
        "family": "personal_domains",
        "parent_path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "target_path": "00_HOME/Personal-Domains/Language-Learning-Global-Mobility.md",
        "target_kind": "personal_domain_node",
        "keywords": ("language", "languages", "mandarin", "hsk", "global mobility", "chinese"),
        "index_targets": ("02_KNOWLEDGE/Language/Language-Learning.md",),
    },
    {
        "id": "mandarin_hsk1",
        "label": "Mandarin / HSK 1",
        "family": "language_child_nodes",
        "parent_path": "00_HOME/Personal-Domains/Language-Learning-Global-Mobility.md",
        "target_path": "01_PROJECTS/Language-Mobility/Mandarin.md",
        "target_kind": "project_and_knowledge_child_node",
        "keywords": ("mandarin", "hsk", "chinese"),
        "index_targets": ("02_KNOWLEDGE/Language/Mandarin-HSK1.md", "01_PROJECTS/Projects-Hub.md"),
    },
    {
        "id": "networking_social_capital",
        "label": "Networking / Social Capital",
        "family": "personal_domains",
        "parent_path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "target_path": "00_HOME/Personal-Domains/Networking-Social-Capital.md",
        "target_kind": "personal_domain_node",
        "keywords": ("networking", "social capital", "linkedin", "twitch", "relationships", "network"),
        "index_targets": ("02_KNOWLEDGE/Networking-Social/Networking-Social-Capital.md",),
    },
    {
        "id": "hardware_robotics",
        "label": "Hardware / Systems / Future Robotics",
        "family": "personal_domains",
        "parent_path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "target_path": "00_HOME/Personal-Domains/Hardware-Systems-Future-Robotics.md",
        "target_kind": "personal_domain_node",
        "keywords": ("hardware", "gpu", "raspberry pi", "edge compute", "robotics", "physical ai"),
        "index_targets": ("02_KNOWLEDGE/Hardware/Hardware-Robotics.md", "01_PROJECTS/GPUHardwareResale/GPUHardwareResale-OS.md"),
    },
    {
        "id": "prompt_engineering",
        "label": "Prompt Engineering",
        "family": "ai_agent_engineering",
        "parent_path": "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md",
        "target_path": "02_KNOWLEDGE/AI-Agents/Prompt-Engineering.md",
        "target_kind": "standalone_knowledge_node",
        "keywords": ("prompt engineering", "prompting", "prompt engineer"),
        "index_targets": ("02_KNOWLEDGE/Knowledge-Index.md",),
    },
    {
        "id": "agent_engineering",
        "label": "Agent Engineering",
        "family": "ai_agent_engineering",
        "parent_path": "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md",
        "target_path": "02_KNOWLEDGE/AI-Agents/Agent-Engineering.md",
        "target_kind": "standalone_knowledge_node",
        "keywords": ("agent engineering", "agents", "agent runtimes", "multi-agent", "tool use"),
        "index_targets": ("02_KNOWLEDGE/Knowledge-Index.md", "06_AGENTS/Agent-Control-Plane.md"),
    },
    {
        "id": "runtime_engineering",
        "label": "Runtime Engineering",
        "family": "ai_agent_engineering",
        "parent_path": "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md",
        "target_path": "02_KNOWLEDGE/AI-Agents/Runtime-Engineering.md",
        "target_kind": "standalone_knowledge_node",
        "keywords": ("runtime engineering", "runtime ops", "agent runtime", "chase os runtime", "chaseos runtime"),
        "index_targets": ("02_KNOWLEDGE/Runtime-Ops/Runtime-Ops.md", "06_AGENTS/Agent-Control-Plane.md"),
    },
    {
        "id": "rag_mcp_source_intelligence",
        "label": "RAG / MCP / Source Intelligence",
        "family": "ai_agent_engineering",
        "parent_path": "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md",
        "target_path": "02_KNOWLEDGE/AI-Agents/Source-Intelligence.md",
        "target_kind": "standalone_knowledge_node",
        "keywords": ("rag", "mcp", "source intelligence", "retrieval", "memory system", "knowledge graph"),
        "index_targets": ("02_KNOWLEDGE/Knowledge-Index.md", "06_AGENTS/Source-Intelligence-Core.md"),
    },
    {
        "id": "university_modules",
        "label": "University / Computer Science Modules",
        "family": "project_operating_files",
        "parent_path": "01_PROJECTS/University/Modules/Modules.md",
        "target_path": "01_PROJECTS/University/Modules/Modules.md",
        "target_kind": "project_module_tree",
        "keywords": ("university", "degree", "module", "computer science", "coursework", "principles of software engineering"),
        "index_targets": ("01_PROJECTS/University/Degree-OS.md", "02_KNOWLEDGE/Computer-Science/Computer-Science.md"),
    },
    {
        "id": "content_creation_youtube_monetization",
        "label": "Content Creation / YouTube Monetization",
        "family": "project_operating_files",
        "parent_path": "01_PROJECTS/ContentEngine/ContentCreation-OS.md",
        "target_path": "01_PROJECTS/ContentEngine/ContentCreation-OS.md",
        "target_kind": "project_operating_node",
        "keywords": ("content creation", "youtube", "youtube monetization", "creator", "personal brand", "chaseintech", "chasersol"),
        "index_targets": ("02_KNOWLEDGE/Content-Distribution/Content-Distribution.md", "01_PROJECTS/Projects-Hub.md"),
    },
    {
        "id": "trading_systems_market_ops",
        "label": "Trading Systems / Market Ops",
        "family": "project_operating_files",
        "parent_path": "01_PROJECTS/Projects-Hub.md",
        "target_path": "01_PROJECTS/TradingSystems/TradingSystems-OS.md",
        "target_kind": "project_operating_node",
        "keywords": ("trading", "market", "crypto", "funding rates", "order flow", "risk management", "indicator"),
        "index_targets": ("02_KNOWLEDGE/Trading-Systems/Trading-Systems-Engineering.md",),
    },
    {
        "id": "cybersecurity_bug_bounty",
        "label": "Cybersecurity / Bug Bounty",
        "family": "project_operating_files",
        "parent_path": "01_PROJECTS/Projects-Hub.md",
        "target_path": "01_PROJECTS/Cybersecurity/Cybersecurity-OS.md",
        "target_kind": "project_operating_node",
        "keywords": ("cybersecurity", "bug bounty", "security", "vulnerability", "pentest", "credential boundary"),
        "index_targets": ("02_KNOWLEDGE/Cybersecurity/Cybersecurity.md",),
    },
    {
        "id": "full_stack_software_engineering",
        "label": "Full-Stack / Software Engineering",
        "family": "project_operating_files",
        "parent_path": "01_PROJECTS/Projects-Hub.md",
        "target_path": "01_PROJECTS/FullStackWeb2Web3/FullStackWeb2Web3-OS.md",
        "target_kind": "project_operating_node",
        "keywords": ("full stack", "software engineering", "react", "backend", "web3", "solana"),
        "index_targets": ("02_KNOWLEDGE/Full-Stack/Full-Stack-Engineering.md",),
    },
    {
        "id": "chaseos_architecture",
        "label": "ChaseOS Architecture",
        "family": "chaseos_runtime",
        "parent_path": "01_PROJECTS/ChaseOS/ChaseOS-OS.md",
        "target_path": "01_PROJECTS/ChaseOS/ChaseOS-OS.md",
        "target_kind": "project_operating_node",
        "keywords": ("chaseos", "chase os", "personal os", "studio", "operator runtime", "agent bus", "workspace mode"),
        "index_targets": ("06_AGENTS/ChaseOS-Studio-Architecture.md", "06_AGENTS/Use-Case-Mode-Architecture.md"),
    },
    {
        "id": "personal_map_candidates",
        "label": "Personal Map Candidate Surface",
        "family": "personal_map_candidates",
        "parent_path": "06_AGENTS/Personal-Map-Architecture.md",
        "target_path": f"{PERSONAL_MAP_CANDIDATE_DIR}/YYYY-MM-DD-personal-context-candidates-review.md",
        "target_kind": "candidate_review_deck",
        "keywords": ("goal", "goals", "preference", "preferences", "routine", "habit", "memory", "profile", "personal map"),
        "index_targets": (PERSONAL_MAP_CANDIDATE_DIR,),
    },
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _today_utc(generated_at: str) -> str:
    return generated_at.split("T", 1)[0]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _safe_slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (slug or fallback)[:96].strip("-") or fallback


def _scan_secrets(source_text: str) -> dict[str, Any]:
    categories: list[str] = []
    redaction_count = 0
    redacted = source_text
    for category, pattern in SECRET_PATTERNS:
        redacted, count = pattern.subn(SECRET_TOKEN, redacted)
        if count:
            categories.append(category)
            redaction_count += count
    return {
        "contains_secret": bool(redaction_count),
        "redaction_count": redaction_count,
        "indicator_categories": list(dict.fromkeys(categories)),
        "source_text_redacted_for_preview": bool(redaction_count),
        "raw_source_text_included_in_payload": False,
        "redacted_text_included_in_payload": False,
    }


def _source_stats(source_text: str) -> dict[str, Any]:
    stripped = source_text.strip()
    return {
        "source_chars": len(source_text),
        "source_lines": 0 if not stripped else source_text.count("\n") + 1,
        "source_words": len(re.findall(r"\b\w+\b", source_text)),
        "source_digest_sha256": _sha256_text(source_text),
        "source_text_stored_in_approval_packet": False,
    }


def _matched_terms(source_lower: str, keywords: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for keyword in keywords:
        lowered = keyword.lower()
        if re.search(rf"(?<![a-z0-9]){re.escape(lowered)}(?![a-z0-9])", source_lower):
            matches.append(keyword)
    return matches


def _node_proposals(source_text: str) -> list[dict[str, Any]]:
    source_lower = source_text.lower()
    proposals: list[dict[str, Any]] = []
    for rule in NODE_RULES:
        keywords = tuple(str(item) for item in rule.get("keywords") or ())
        matches = _matched_terms(source_lower, keywords)
        if not matches:
            continue
        proposals.append(
            {
                "id": f"personal-context-node-{rule['id']}",
                "rule_id": rule["id"],
                "label": rule["label"],
                "family": rule["family"],
                "parent_path": rule["parent_path"],
                "target_path": rule["target_path"],
                "target_kind": rule["target_kind"],
                "index_targets": list(rule.get("index_targets") or ()),
                "matched_terms": matches,
                "evidence_basis": "source_term_match",
                "trust_posture": "SOURCE-DERIVED / REVIEW REQUIRED",
                "write_state": "proposed_only",
                "requires_operator_review": True,
            }
        )
    if not proposals and source_text.strip():
        proposals.append(
            {
                "id": "personal-context-node-manual-review",
                "rule_id": "manual_review_required",
                "label": "Manual Personal Context Review",
                "family": "manual_review",
                "parent_path": "00_HOME/Personal-Operator-Index.md",
                "target_path": "03_INPUTS/Personal-Context-Intake/Personal-Context-Manual-Review.md",
                "target_kind": "manual_review_route",
                "index_targets": ["00_HOME/Personal-Operator-Index.md"],
                "matched_terms": [],
                "evidence_basis": "source_present_no_rule_match",
                "trust_posture": "SOURCE-DERIVED / MANUAL REVIEW REQUIRED",
                "write_state": "proposed_only",
                "requires_operator_review": True,
            }
        )
    return proposals


def _edge_proposals(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for node in nodes:
        edges.append(
            {
                "id": f"edge:{node['rule_id']}:parent-child",
                "source": node["parent_path"],
                "target": node["target_path"],
                "relation": "parent_child_route",
                "family": node["family"],
                "trust_posture": "SOURCE-DERIVED / REVIEW REQUIRED",
                "write_state": "proposed_only",
            }
        )
        edges.append(
            {
                "id": f"edge:{node['rule_id']}:operator-index",
                "source": "00_HOME/Personal-Operator-Index.md",
                "target": node["target_path"],
                "relation": "operator_context_route",
                "family": node["family"],
                "trust_posture": "SOURCE-DERIVED / REVIEW REQUIRED",
                "write_state": "proposed_only",
            }
        )
    return edges


def _planned_artifacts(today: str, proposal_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "raw_context_source",
            "path": f"{RAW_INTAKE_DIR}/{today}_personal-context-source.md",
            "operation": "future_create_raw_intake_file",
            "contains_raw_source_text": True,
            "written_by_this_surface": False,
            "requires_future_executor": True,
        },
        {
            "id": "source_digest",
            "path": f"{RAW_INTAKE_DIR}/{today}_personal-context-source-digest.md",
            "operation": "future_create_source_digest",
            "contains_raw_source_text": False,
            "written_by_this_surface": False,
            "requires_future_executor": True,
        },
        {
            "id": "node_coverage_audit",
            "path": f"{RAW_INTAKE_DIR}/{today}_personal-context-node-coverage-audit.md",
            "operation": "future_create_node_coverage_audit",
            "contains_raw_source_text": False,
            "written_by_this_surface": False,
            "requires_future_executor": True,
        },
        {
            "id": "index_patch_preview",
            "path": f"{RAW_INTAKE_DIR}/{today}_personal-context-index-patch-preview.md",
            "operation": "future_create_index_patch_preview",
            "contains_raw_source_text": False,
            "written_by_this_surface": False,
            "requires_future_executor": True,
        },
        {
            "id": "personal_map_candidate_log",
            "path": f"{PERSONAL_MAP_CANDIDATE_DIR}/{today}-personal-context-candidates.jsonl",
            "operation": "future_stage_personal_map_candidate_log",
            "contains_raw_source_text": False,
            "written_by_this_surface": False,
            "requires_future_executor": True,
        },
        {
            "id": "personal_map_candidate_review",
            "path": f"{PERSONAL_MAP_CANDIDATE_DIR}/{today}-personal-context-candidates-review.md",
            "operation": "future_stage_personal_map_candidate_review",
            "contains_raw_source_text": False,
            "written_by_this_surface": False,
            "requires_future_executor": True,
        },
        {
            "id": "approval_preview_packet",
            "path": f"{PREVIEW_ROOT}/{proposal_id}.json",
            "operation": "approval_queue_target_preview_only",
            "contains_raw_source_text": False,
            "written_by_this_surface": False,
            "requires_future_executor": False,
        },
    ]


def _index_patch_plan(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required_targets = {
        "00_HOME/Personal-Operator-Index.md": "route_imported_context",
        "00_HOME/Dashboard.md": "surface_import_status",
        "00_HOME/Operating-System.md": "route_personal_domain_updates",
        "01_PROJECTS/Projects-Hub.md": "route_project_child_nodes",
        CANONICAL_KNOWLEDGE_INDEX_PATH: "route_knowledge_child_nodes",
        ROOT_KNOWLEDGE_SHIM_PATH: "preserve_routing_shim_only",
        "00_HOME/Personal-Domains/Personal-Domains-Index.md": "route_life_domain_child_nodes",
        "06_AGENTS/Personal-Map-Architecture.md": "document_candidate_boundary",
    }
    for node in nodes:
        for target in node.get("index_targets") or []:
            required_targets.setdefault(str(target), "route_source_derived_child_node")
    return [
        {
            "target_path": path,
            "operation": operation,
            "write_state": "proposed_only",
            "requires_operator_review": True,
            "canonical_mutation_performed": False,
        }
        for path, operation in sorted(required_targets.items())
    ]


def _build_preview_packet(
    *,
    source_text: str,
    source_label: str,
    operator_id: str,
    generated_at: str,
) -> dict[str, Any]:
    stats = _source_stats(source_text)
    nodes = _node_proposals(source_text)
    edges = _edge_proposals(nodes)
    today = _today_utc(generated_at)
    digest_basis = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "source_digest_sha256": stats["source_digest_sha256"],
        "source_label": source_label,
        "node_routes": [
            {
                "rule_id": node["rule_id"],
                "target_path": node["target_path"],
                "matched_terms": node["matched_terms"],
            }
            for node in nodes
        ],
        "edge_count": len(edges),
        "operator_id": operator_id or "studio-operator",
    }
    import_preview_digest = _sha256_text(_canonical_json(digest_basis))
    proposal_id = f"personal-context-import-preview-{import_preview_digest[:16]}"
    artifacts = _planned_artifacts(today, proposal_id)
    return {
        "proposal_id": proposal_id,
        "schema_version": MODEL_VERSION,
        "status": "pending_approval_preview",
        "source_label": source_label,
        "source_digest_sha256": stats["source_digest_sha256"],
        "source_stats": stats,
        "source_text_included": False,
        "source_text_storage_policy": "approval packet stores digest, stats, matched route terms, and proposed paths only; future executor must receive matching source text again before raw intake writes",
        "node_proposals": nodes,
        "edge_proposals": edges,
        "index_patch_plan": _index_patch_plan(nodes),
        "planned_artifacts": artifacts,
        "approval_required_before_effect": True,
        "raw_context_file_written": False,
        "source_digest_file_written": False,
        "node_coverage_audit_written": False,
        "index_patch_preview_written": False,
        "personal_map_candidates_written": False,
        "dashboard_updated": False,
        "personal_operator_index_updated": False,
        "projects_hub_updated": False,
        "knowledge_index_updated": False,
        "root_knowledge_index_role": "routing_shim_not_canonical",
        "provider_call_performed": False,
        "agent_bus_task_written": False,
        "runtime_memory_mutated": False,
        "canonical_mutation_allowed": False,
        "import_preview_digest": import_preview_digest,
        "digest_basis_sha256": _sha256_text(_canonical_json(digest_basis)),
        "target_path": f"{PREVIEW_ROOT}/{proposal_id}.json",
    }


def _find_existing(vault: Path, import_preview_digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active_statuses = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("personal_context_import_preview_digest") != import_preview_digest:
            continue
        if str(payload.get("status") or "") not in active_statuses:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
            "target_path": spec.get("target_path"),
        }
    return None


def _approval_spec(*, packet: dict[str, Any], operator_id: str) -> ActionSpec:
    content_packet = {
        "record_type": "personal_context_import_preview_packet",
        "schema_version": MODEL_VERSION,
        "proposal_packet": packet,
        "source_text_included": False,
        "raw_source_text_included": False,
        "future_executor_requires_matching_source_digest": True,
    }
    content = json.dumps(content_packet, indent=2, sort_keys=True) + "\n"
    return ActionSpec(
        action_type="create_file",
        target_path=str(packet.get("target_path") or ""),
        content=content,
        metadata={
            "pass": PASS_ID,
            "source_surface": SURFACE_ID,
            "personal_context_import_preview_writer": True,
            "personal_context_import_preview_execution_blocked": True,
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": NEXT_RECOMMENDED_PASS,
            "required_approval_class": APPROVAL_CLASS,
            "personal_context_import_preview_digest": packet.get("import_preview_digest"),
            "personal_context_import_source_sha256": packet.get("source_digest_sha256"),
            "proposal_id": packet.get("proposal_id"),
            "node_proposal_count": len(packet.get("node_proposals") or []),
            "edge_proposal_count": len(packet.get("edge_proposals") or []),
            "raw_context_file_written": False,
            "source_digest_file_written": False,
            "node_coverage_audit_written": False,
            "index_patch_preview_written": False,
            "personal_map_candidates_written": False,
            "dashboard_updated": False,
            "personal_operator_index_updated": False,
            "projects_hub_updated": False,
            "knowledge_index_updated": False,
            "provider_call_performed": False,
            "agent_bus_task_written": False,
            "runtime_memory_mutated": False,
            "canonical_mutation_allowed": False,
            "source_text_included": False,
        },
        submitted_by=operator_id or "studio-operator",
        note="Personal context import preview approval request; target effects deferred.",
    )


def _write_audit_record(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    packet: dict[str, Any],
    operator_id: str,
) -> str:
    root = vault / AUDIT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    digest = str(packet.get("import_preview_digest") or "missing")
    path = root / f"{digest}.json"
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "recorded_at_utc": _now_utc(),
        "approval_id": approval_id,
        "approval_artifact_path": approval_path,
        "approval_status": "pending",
        "proposal_id": packet.get("proposal_id"),
        "import_preview_digest": digest,
        "source_digest_sha256": packet.get("source_digest_sha256"),
        "source_text_included": False,
        "node_proposal_count": len(packet.get("node_proposals") or []),
        "edge_proposal_count": len(packet.get("edge_proposals") or []),
        "operator_id": operator_id or "studio-operator",
        "raw_context_file_written": False,
        "personal_map_candidates_written": False,
        "canonical_mutation_allowed": False,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _rel(vault, path)


def _authority(created: bool) -> dict[str, Any]:
    return {
        "approval_queue_write_allowed_with_digest": True,
        "approval_queue_write_performed": bool(created),
        "approval_execution_allowed": False,
        "raw_context_file_write_allowed": False,
        "source_digest_file_write_allowed": False,
        "node_coverage_audit_write_allowed": False,
        "index_patch_preview_write_allowed": False,
        "personal_map_candidate_write_allowed": False,
        "personal_map_apply_allowed": False,
        "dashboard_write_allowed": False,
        "personal_operator_index_write_allowed": False,
        "projects_hub_write_allowed": False,
        "knowledge_index_write_allowed": False,
        "provider_calls_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_memory_mutation_allowed": False,
        "credential_values_visible": False,
        "source_text_stored_in_approval_packet": False,
        "canonical_mutation_allowed": False,
    }


def build_personal_context_import_preview_writer(
    vault_root: str | Path,
    *,
    source_text: str | None = None,
    source_label: str | None = None,
    expected_import_preview_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "studio-operator",
) -> dict[str, Any]:
    """Preview or queue a future personal-context import approval request."""

    vault = Path(vault_root).resolve()
    generated_at = _now_utc()
    raw_source = str(source_text or "")
    label = _safe_slug(str(source_label or "").strip() or "operator-context-import", "operator-context-import")
    expected = str(expected_import_preview_digest or "").strip()
    blockers: list[str] = []
    warnings: list[str] = []

    if not raw_source.strip():
        blockers.append("source_text_required_for_import_preview")
    if len(raw_source) > SOURCE_TEXT_MAX_CHARS:
        blockers.append("source_text_exceeds_preview_limit")

    secret_screen = _scan_secrets(raw_source)
    if secret_screen["contains_secret"]:
        blockers.append("secret_or_credential_indicator_present")

    packet = _build_preview_packet(
        source_text=raw_source,
        source_label=label,
        operator_id=operator_id,
        generated_at=generated_at,
    )
    digest = str(packet.get("import_preview_digest") or "")

    if write_approval and not expected:
        blockers.append("expected_import_preview_digest_required")
    elif write_approval and expected != digest:
        blockers.append("expected_import_preview_digest_mismatch")

    duplicate = _find_existing(vault, digest) if digest else None
    if write_approval and duplicate:
        blockers.append("approval_queue_request_already_exists_for_digest")

    action_spec = _approval_spec(packet=packet, operator_id=operator_id)
    validation = StudioService(vault).validate_action(action_spec)
    if validation.gate_blocked:
        blockers.append("studio_service_validation_gate_blocked")
        warnings.extend(str(item) for item in validation.errors)
    warnings.extend(str(item) for item in validation.warnings)

    blocked_unique = list(dict.fromkeys(blockers))
    created = False
    queue_writer_called = False
    approval_id: str | None = None
    approval_path: str | None = None
    audit_path: str | None = None
    status = STATUS_PREVIEW if not blocked_unique else BLOCKED_STATUS

    if write_approval and not blocked_unique:
        queue_writer_called = True
        request = StudioService(vault).queue_for_approval(action_spec)
        created = True
        approval_id = request.approval_id
        approval_path = f"{StudioService.APPROVAL_DIR}/{request.approval_id}.json"
        audit_path = _write_audit_record(
            vault=vault,
            approval_id=approval_id,
            approval_path=approval_path,
            packet=packet,
            operator_id=operator_id,
        )
        status = STATUS_WRITTEN

    return {
        "ok": not blocked_unique,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": generated_at,
        "vault_root": str(vault),
        "read_only": not created,
        "approval_gated": True,
        "summary": {
            "source_label": label,
            "proposal_id": packet.get("proposal_id"),
            "node_proposal_count": len(packet.get("node_proposals") or []),
            "edge_proposal_count": len(packet.get("edge_proposals") or []),
            "index_patch_target_count": len(packet.get("index_patch_plan") or []),
            "planned_artifact_count": len(packet.get("planned_artifacts") or []),
            "queue_write_preview_ready": not blocked_unique,
            "write_approval_requested": bool(write_approval),
            "approval_request_created": created,
            "approval_queue_writer_called": queue_writer_called,
            "approval_status": "pending" if created else None,
            "duplicate_active_request_present": bool(duplicate),
            "source_text_included_in_approval_packet": False,
            "raw_context_file_written": False,
            "source_digest_file_written": False,
            "node_coverage_audit_written": False,
            "index_patch_preview_written": False,
            "personal_map_candidates_written": False,
            "canonical_mutation_performed": False,
            "provider_call_performed": False,
            "agent_bus_task_written": False,
            "runtime_memory_mutated": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(blocked_unique),
        },
        "digest_proof": {
            "import_preview_digest": digest,
            "expected_import_preview_digest": expected or None,
            "expected_digest_matched": expected == digest if expected else None,
            "digest_required_for_write": True,
            "source_digest_sha256": packet.get("source_digest_sha256"),
            "digest_basis_sha256": packet.get("digest_basis_sha256"),
        },
        "secret_screen": secret_screen,
        "proposal_packet_preview": packet,
        "approval_queue_write": {
            "queue_writer": "runtime.studio.service.StudioService.queue_for_approval",
            "queue_writer_called": queue_writer_called,
            "approval_request_created": created,
            "approval_status_now": "pending" if created else None,
            "approval_artifact_path": approval_path,
            "duplicate": duplicate,
        },
        "approval_record": {
            "approval_id": approval_id,
            "approval_path": approval_path,
            "approval_status": "pending" if created else None,
            "duplicate": duplicate,
        },
        "audit_record": {
            "audit_record_written": bool(audit_path),
            "audit_record_path": audit_path,
        },
        "target_write_proof": {
            "target_path": packet.get("target_path"),
            "target_file_exists_after": (vault / str(packet.get("target_path") or "")).exists(),
            "target_file_written": False,
            "raw_context_file_written": False,
            "personal_map_candidates_written": False,
            "canonical_mutation_performed": False,
        },
        "service_validation": {
            "valid": validation.valid,
            "gate_blocked": validation.gate_blocked,
            "approval_required": True,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        },
        "approval_center_visibility": {
            "source_group": "studio-service",
            "visible_after_write": created,
            "approval_center_reads_runtime_studio_approvals": True,
        },
        "authority": _authority(created),
        "readiness": {
            "personal_context_import_preview_writer_ready": not blocked_unique,
            "personal_context_import_approval_queue_write_gated": True,
            "personal_context_import_digest_required": True,
            "personal_context_import_source_text_required": True,
            "personal_context_import_source_text_not_stored_in_approval_packet": True,
            "personal_context_import_raw_writes_blocked": True,
            "personal_context_import_canonical_writes_blocked": True,
            "personal_context_import_approved_executor_required": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "denied_by_this_surface": [
            "approval_grant_or_reject",
            "approval_consumption",
            "approval_execution",
            "raw_context_file_write",
            "source_digest_file_write",
            "node_coverage_audit_write",
            "index_patch_preview_write",
            "personal_map_candidate_write",
            "personal_map_apply",
            "dashboard_write",
            "personal_operator_index_write",
            "projects_hub_write",
            "knowledge_index_write",
            "provider_api_call",
            "runtime_dispatch",
            "agent_bus_task_write",
            "runtime_memory_mutation",
            "credential_value_display",
            "canonical_writeback",
        ],
        "blocked_reasons": blocked_unique,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_personal_context_import_preview_writer(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    approval = payload.get("approval_record") or {}
    lines = [
        "Personal Context Import Preview Writer",
        f"Status: {payload.get('status')}",
        f"Proposal id: {summary.get('proposal_id') or 'missing'}",
        f"Node proposals: {summary.get('node_proposal_count')}",
        f"Edge proposals: {summary.get('edge_proposal_count')}",
        f"Approval request created: {summary.get('approval_request_created')}",
        f"Approval id: {approval.get('approval_id') or 'none'}",
        f"Import preview digest: {digest.get('import_preview_digest') or 'missing'}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
