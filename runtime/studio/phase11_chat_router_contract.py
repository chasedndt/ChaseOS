"""Read-only Phase 11 chat router intent contract.

This is a pre-implementation contract for the ChaserOS conversational command
router. It classifies a message with deterministic rules only, consumes the
provider routing consumer contract for model-bound intents, and never executes a
model call, runtime task, browser task, approval action, or vault write.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import re
from typing import Any

from runtime.providers.routing_consumer_contract import build_provider_routing_consumer_contract
from runtime.studio.phase11_chat_safety_policy import build_phase11_chat_safety_policy


MODEL_VERSION = "studio.phase11_chat_router_contract.v1"
SURFACE_ID = "phase11_chat_router_readonly_intent_contract"

KNOWN_INTENTS = [
    "chat-answer",
    "project-create",
    "project-update",
    "vault-node-create",
    "vault-node-update",
    "source-note",
    "synthesis-note",
    "rnd-entry",
    "roadmap-item",
    "runtime-task",
    "browser-task",
    "scheduled-workflow",
    "model-chat",
    "approval-action",
    "memory-save",
    "handoff",
    "archive",
    "dashboard-query",
]

MODEL_BOUND_INTENTS = {"chat-answer", "model-chat", "synthesis-note"}
PROPOSAL_INTENTS = {
    "project-create",
    "project-update",
    "vault-node-create",
    "vault-node-update",
    "source-note",
    "synthesis-note",
    "rnd-entry",
    "roadmap-item",
    "memory-save",
    "handoff",
    "archive",
}
APPROVAL_REQUIRED_INTENTS = {
    "project-create",
    "project-update",
    "vault-node-create",
    "vault-node-update",
    "source-note",
    "runtime-task",
    "browser-task",
    "scheduled-workflow",
    "approval-action",
    "memory-save",
    "handoff",
    "archive",
}

SLASH_INTENT_MAP = {
    "/map": "dashboard-query",
    "/vault": "dashboard-query",
    "/dashboard": "dashboard-query",
    "/runtime": "dashboard-query",
    "/models": "dashboard-query",
    "/provider": "dashboard-query",
    "/log": "dashboard-query",
    "/run": "runtime-task",
    "/agent": "runtime-task",
    "/browser": "browser-task",
    "/schedule": "scheduled-workflow",
    "/approve": "approval-action",
    "/reject": "approval-action",
    "/new-project": "project-create",
    "/new-node": "vault-node-create",
    "/memory": "memory-save",
    "/handoff": "handoff",
    "/archive": "archive",
    "/rnd": "rnd-entry",
    "/pet": "dashboard-query",
    "/companion": "handoff",
}

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous",
    "system prompt",
    "developer message",
    "reveal secrets",
    "print secrets",
    "show credentials",
    "bypass gate",
    "disable approval",
    "without approval",
]

DENIED_SIDE_EFFECT_PATTERNS = {
    "vault_write": [r"\b(write|edit|update|mutate|modify|create)\b.*\b(vault|file|note|node)\b"],
    "lifecycle_execution": [r"\b(start|stop|restart|run)\b.*\b(runtime|agent|workflow)\b"],
    "runtime_dispatch": [r"\b(dispatch|run|start|enqueue)\b.*\b(hermes|openclaw|codex|archon|runtime|agent|workflow)\b"],
    "browser_or_shell_or_connector_authority": [
        r"\b(browser|shell|terminal|connector|api call|provider api|call provider|call a connector|launch browser|use shell|connect cdp|cdp)\b"
    ],
    "approval_consumption": [r"\b(consume|execute|grant|approve|reject)\b.*\bapproval\b"],
    "protected_file_write": [r"\bprotected file\b", r"\b(permission matrix|trust tier|gate rule|security doctrine)\b"],
    "hidden_memory_write": [r"\b(save|write|store|persist)\b.*\b(hidden memory|memory|conversation memory)\b"],
    "credential_or_config_mutation": [r"\b(mutate|edit|change|set|write|update)\b.*\b(credential|credentials|config|provider key|api key|provider config)\b"],
    "source_pack_promotion": [r"\b(promote|publish|apply)\b.*\bsource pack\b"],
    "graph_mutation": [r"\b(edit|mutate|write|update|change)\b.*\bgraph\b"],
    "canonical_knowledge_promotion": [r"\b(promote|publish|write|apply)\b.*\bcanonical knowledge\b"],
}

BACKEND_DEPENDENCIES = [
    {
        "dependency_key": "protected_file_write",
        "missing_contract": "protected-file Gate write contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat read-only surface",
        "lower_phase_owner_or_surface": "Permission Matrix / Gate protected-file workflow",
        "minimum_proof_needed": "operator-approved protected-file packet plus no-write preflight",
        "blocked_action_reason": "protected file writes are outside Phase 11 Chat authority",
    },
    {
        "dependency_key": "runtime_dispatch",
        "missing_contract": "Agent Bus/AOR dispatch contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat runtime dispatch readiness",
        "lower_phase_owner_or_surface": "runtime/agent_bus and AOR workflow manifests",
        "minimum_proof_needed": "structured task packet, approval envelope, and dispatch executor proof",
        "blocked_action_reason": "runtime dispatch is preview-only from Chat",
    },
    {
        "dependency_key": "browser_shell_connector_authority",
        "missing_contract": "browser/shell/connector execution contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat browser/provider readiness",
        "lower_phase_owner_or_surface": "Phase 9 runtime adapter / connector governance",
        "minimum_proof_needed": "scoped executor contract, credentials policy, and operator approval",
        "blocked_action_reason": "browser, shell, connector, and provider execution are unavailable",
    },
    {
        "dependency_key": "approval_consumption_execution",
        "missing_contract": "approval consumption and exact-once marker contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat approval consumption readiness",
        "lower_phase_owner_or_surface": "Gate approval consumer policy",
        "minimum_proof_needed": "approved consumption artifact, replay guard, and marker proof",
        "blocked_action_reason": "approval consumption cannot be performed by Chat",
    },
    {
        "dependency_key": "credential_config_mutation",
        "missing_contract": "settings/provider config writer contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat provider/settings posture",
        "lower_phase_owner_or_surface": "Studio Settings / Provider / Runtime Config panels",
        "minimum_proof_needed": "redacted config diff, approval, rollback proof, and no-secret rendering test",
        "blocked_action_reason": "credential and configuration mutation is blocked",
    },
    {
        "dependency_key": "source_pack_creation_promotion",
        "missing_contract": "source-pack promotion contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat source-pack denial UX",
        "lower_phase_owner_or_surface": "source-pack promotion pipeline and Gate",
        "minimum_proof_needed": "validated source pack, approval decision, and promotion audit",
        "blocked_action_reason": "source-pack promotion is not available in Chat",
    },
    {
        "dependency_key": "graph_canonical_mutation",
        "missing_contract": "graph/canonical mutation policy",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat graph context display",
        "lower_phase_owner_or_surface": "canonical graph maintenance workflow",
        "minimum_proof_needed": "graph delta contract, provenance proof, and Gate review",
        "blocked_action_reason": "graph and canonical mutations are read-only from Chat",
    },
    {
        "dependency_key": "canonical_knowledge_promotion",
        "missing_contract": "canonical knowledge promotion Gate contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat canonical promotion denial UX",
        "lower_phase_owner_or_surface": "ChaseOS Gate and canonical knowledge promotion workflow",
        "minimum_proof_needed": "candidate artifact, provenance proof, Gate decision, and Agent-Activity audit",
        "blocked_action_reason": "canonical knowledge promotion is unavailable from Chat",
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _first_slash_token(message: str) -> str | None:
    if not message.startswith("/"):
        return None
    token = message.split(maxsplit=1)[0].strip().lower()
    return token or None


def classify_phase11_intent(message: str | None, explicit_intent: str | None = None) -> dict[str, Any]:
    """Classify a chat message without an LLM call."""

    normalized = _norm(message)
    lowered = normalized.lower()

    if explicit_intent:
        intent = explicit_intent.strip()
        if intent not in KNOWN_INTENTS:
            intent = "chat-answer"
        return {
            "intent_class": intent,
            "confidence": "operator_declared" if explicit_intent in KNOWN_INTENTS else "fallback",
            "classifier": "operator_declared_intent",
            "llm_classifier_used": False,
            "matched_rule": "explicit_intent",
        }

    slash = _first_slash_token(normalized)
    if slash:
        intent = SLASH_INTENT_MAP.get(slash, "dashboard-query")
        return {
            "intent_class": intent,
            "confidence": "medium",
            "classifier": "deterministic_rule_stub",
            "llm_classifier_used": False,
            "matched_rule": f"slash:{slash}",
        }

    keyword_rules = [
        ("project-create", r"\b(new|create|start|spin up)\b.*\b(project|venture|app|tool)\b"),
        ("vault-node-create", r"\b(create|new|add)\b.*\b(note|node|knowledge note|source note)\b"),
        ("project-update", r"\b(update|change|revise)\b.*\b(project|project-os|status)\b"),
        ("runtime-task", r"\b(run|dispatch|start)\b.*\b(operator_today|operator_close_day|workflow|runtime)\b"),
        ("browser-task", r"\b(browser|screenshot|open url|click|navigate)\b"),
        ("scheduled-workflow", r"\b(schedule|cron|weekly|daily digest|remind)\b"),
        ("approval-action", r"\b(approve|reject|deny)\b.*\b(approval|request|packet)\b"),
        ("memory-save", r"\b(save|remember|store)\b.*\b(memory|conversation|context)\b"),
        ("handoff", r"\b(handoff|hand off|ask hermes|ask openclaw|send to)\b"),
        ("rnd-entry", r"\b(r&d|rnd|feature idea|we should add|wouldn't it be good)\b"),
        ("roadmap-item", r"\b(roadmap|backlog)\b"),
        ("model-chat", r"\b(model|provider|gpt|claude|openai|anthropic|ollama)\b"),
        ("dashboard-query", r"\b(show|list|status|what is|what's|dashboard|summary)\b"),
    ]
    for intent, pattern in keyword_rules:
        if re.search(pattern, lowered):
            return {
                "intent_class": intent,
                "confidence": "low",
                "classifier": "deterministic_rule_stub",
                "llm_classifier_used": False,
                "matched_rule": f"keyword:{intent}",
            }

    return {
        "intent_class": "chat-answer",
        "confidence": "fallback",
        "classifier": "deterministic_rule_stub",
        "llm_classifier_used": False,
        "matched_rule": "default_chat_answer",
    }


def _untrusted_input_report(message: str) -> dict[str, Any]:
    lowered = message.lower()
    indicators = [pattern for pattern in INJECTION_PATTERNS if pattern in lowered]
    requested_denied_actions = [
        action
        for action, patterns in DENIED_SIDE_EFFECT_PATTERNS.items()
        if any(re.search(pattern, lowered) for pattern in patterns)
    ]
    return {
        "input_treated_as_untrusted": True,
        "embedded_instruction_execution_allowed": False,
        "prompt_injection_indicators": indicators,
        "prompt_injection_suspected": bool(indicators),
        "requested_denied_actions": requested_denied_actions,
        "denied_side_effect_prompt_present": bool(requested_denied_actions),
        "max_message_chars_inspected": min(len(message), 5000),
    }


def _action_spec_report(message: str) -> dict[str, Any]:
    lowered = message.lower().strip()
    vague_patterns = [
        r"^handle (the|this) thing$",
        r"^run (the|this) thing$",
        r"^do (the|this|it)$",
        r"^take care of (it|this)$",
    ]
    ambiguous = any(re.search(pattern, lowered) for pattern in vague_patterns)
    return {
        "ambiguity": {
            "requires_operator_clarification": ambiguous,
            "reason": "ambiguous Phase 11 Chat command lacks a bounded target/action" if ambiguous else None,
            "clarification_required_before_routing": ambiguous,
        },
        "side_effect_targets_declared": False,
    }


def _route_family(intent: str) -> str:
    if intent in {"chat-answer", "model-chat", "synthesis-note"}:
        return "model_bound_readonly"
    if intent == "dashboard-query":
        return "read_only_system_query"
    if intent in {"runtime-task", "scheduled-workflow"}:
        return "approval_gated_runtime_action"
    if intent == "browser-task":
        return "approval_gated_browser_action"
    if intent == "approval-action":
        return "approval_surface_action"
    if intent in PROPOSAL_INTENTS:
        return "proposal_only"
    return "unknown"


def _next_surface(intent: str) -> str:
    return {
        "chat-answer": "provider_routing_consumer_contract",
        "model-chat": "provider_routing_consumer_contract",
        "synthesis-note": "provider_routing_consumer_contract_then_draft_output",
        "dashboard-query": "read_only_dashboard_adapter_future",
        "runtime-task": "approval_gate_then_aor_or_agent_bus_future",
        "browser-task": "approval_gate_then_browser_runtime_future",
        "scheduled-workflow": "approval_gate_then_schedule_intent_future",
        "approval-action": "studio_service_approval_surface_future",
        "project-create": "proposal_card_future",
        "project-update": "proposal_card_future",
        "vault-node-create": "proposal_card_future",
        "vault-node-update": "proposal_card_future",
        "source-note": "quarantine_capture_proposal_future",
        "memory-save": "memory_write_proposal_future",
        "handoff": "agent_bus_proposal_future",
        "archive": "conversation_archive_proposal_future",
        "rnd-entry": "rnd_proposal_future",
        "roadmap-item": "roadmap_proposal_future",
    }.get(intent, "manual_review")


BACKEND_DEPENDENCY_CATALOG: dict[str, dict[str, str]] = {
    "lifecycle_execution": {
        "missing_contract": "runtime lifecycle execution contract for start/stop/run actions",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat runtime/action preview surface",
        "lower_phase_owner_or_surface": "Phase 9 AOR lifecycle policy + runtime/agent_bus dispatch foundation",
        "minimum_proof_needed": "registered runtime manifest, lifecycle policy check, Gate approval record, and audited dry-run dispatch proof",
        "blocked_action_reason": "Phase 11 chat may describe lifecycle intent but cannot start, stop, run, or enqueue runtimes",
    },
    "runtime_dispatch": {
        "missing_contract": "agent_bus runtime dispatch packet creation and claim/execute contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat handoff/runtime task preview surface",
        "lower_phase_owner_or_surface": "runtime/agent_bus router plus AOR workflow foundation",
        "minimum_proof_needed": "schema-valid packet preview, eligible runtime route, approval envelope where required, and non-chat execution consumer",
        "blocked_action_reason": "chat/router output is inspectable state only and must not dispatch executable work",
    },
    "approval_consumption_execution": {
        "missing_contract": "approval consumption/execution contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat approval action surface",
        "lower_phase_owner_or_surface": "Gate/AOR approval queue and Studio service approval consumer",
        "minimum_proof_needed": "approval object lookup, one-shot consumption semantics, audit event, and denied replay proof",
        "blocked_action_reason": "Phase 11 chat may show requested approval action but cannot approve, reject, grant, or consume approvals",
    },
    "source_pack_creation_promotion": {
        "missing_contract": "source-pack creation/promotion contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat source capture/promotion preview surface",
        "lower_phase_owner_or_surface": "source-pack pipeline plus ChaseOS Gate promotion lane",
        "minimum_proof_needed": "quarantine source ref, source-pack schema validation, Gate approval, promotion audit path",
        "blocked_action_reason": "chat/router cannot create, publish, apply, or promote source packs",
    },
    "graph_canonical_mutation": {
        "missing_contract": "graph canonical mutation contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat graph action preview surface",
        "lower_phase_owner_or_surface": "graph mutation policy and canonical vault writeback foundation",
        "minimum_proof_needed": "typed graph diff preview, protected-file policy check, Gate approval, reversible audit trail",
        "blocked_action_reason": "chat/router cannot mutate canonical graph state",
    },
    "browser_shell_connector_authority": {
        "missing_contract": "browser/shell/connector authority contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat external-control request surface",
        "lower_phase_owner_or_surface": "SiteOps browser policy, shell policy, connector manifests, and AOR execution boundary",
        "minimum_proof_needed": "allowlisted target, visible control HUD where applicable, explicit approval, and scoped audit evidence",
        "blocked_action_reason": "chat/router cannot operate browser, shell, terminal, connector, or live external APIs",
    },
    "credential_config_mutation": {
        "missing_contract": "credential/config mutation contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Settings/Chat config request preview surface",
        "lower_phase_owner_or_surface": "provider/settings policy, credential boundary SOP, and owner approval lane",
        "minimum_proof_needed": "redacted config diff, secret non-disclosure proof, owner approval, rollback/audit record",
        "blocked_action_reason": "chat/router cannot read, expose, set, mutate, or persist credentials/config",
    },
    "protected_file_write": {
        "missing_contract": "protected-file write contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat protected-doc proposal surface",
        "lower_phase_owner_or_surface": "Permission Matrix + protected-file approval workflow",
        "minimum_proof_needed": "exact target file, diff preview, explicit protected-file approval, and post-write audit",
        "blocked_action_reason": "chat/router cannot write protected files or expand governance authority",
    },
    "canonical_knowledge_promotion": {
        "missing_contract": "canonical knowledge promotion contract",
        "affected_phase10_or_phase11_surface": "Phase 10/11 Studio Chat knowledge promotion preview surface",
        "lower_phase_owner_or_surface": "ChaseOS Gate and canonical knowledge writeback foundation",
        "minimum_proof_needed": "source lineage, proposed canonical diff, Gate approval, and Agent-Activity/writeback audit",
        "blocked_action_reason": "chat/router cannot promote or write canonical knowledge",
    },
}

_DENIED_ACTION_TO_DEPENDENCY = {
    "vault_write": "protected_file_write",
    "lifecycle_execution": "lifecycle_execution",
    "runtime_dispatch": "runtime_dispatch",
    "browser_or_shell_or_connector_authority": "browser_shell_connector_authority",
    "approval_consumption": "approval_consumption_execution",
    "protected_file_write": "protected_file_write",
    "hidden_memory_write": "canonical_knowledge_promotion",
    "credential_or_config_mutation": "credential_config_mutation",
    "source_pack_promotion": "source_pack_creation_promotion",
    "graph_mutation": "graph_canonical_mutation",
    "canonical_knowledge_promotion": "canonical_knowledge_promotion",
}


def _affected_surfaces(intent: str, requested_denied_actions: list[str]) -> list[str]:
    surfaces = ["Phase 11 Chat"]
    if intent in MODEL_BOUND_INTENTS:
        surfaces.append("runtime/providers")
    if intent in {"runtime-task", "scheduled-workflow", "handoff"} or "runtime_dispatch" in requested_denied_actions:
        surfaces.append("runtime/agent_bus")
        surfaces.append("AOR/Gate")
    if intent == "browser-task" or "browser_or_shell_or_connector_authority" in requested_denied_actions:
        surfaces.append("SiteOps/browser-shell-connector authority")
    if intent in {"project-create", "project-update", "vault-node-create", "vault-node-update", "source-note", "synthesis-note", "rnd-entry", "roadmap-item"}:
        surfaces.append("Studio proposal cards")
    if any(action in requested_denied_actions for action in {"graph_mutation", "canonical_knowledge_promotion", "protected_file_write", "source_pack_promotion"}):
        surfaces.append("ChaseOS Gate/canonical writeback")
    return list(dict.fromkeys(surfaces))


def _required_approvals(intent: str, requested_denied_actions: list[str]) -> list[str]:
    approvals: list[str] = []
    if intent in APPROVAL_REQUIRED_INTENTS or requested_denied_actions:
        approvals.append("operator_approval")
    if any(action in requested_denied_actions for action in {"protected_file_write", "canonical_knowledge_promotion", "source_pack_promotion", "graph_mutation"}):
        approvals.append("chaseos_gate_approval")
    if "credential_or_config_mutation" in requested_denied_actions:
        approvals.append("owner_config_approval")
    return list(dict.fromkeys(approvals))


def _authority_class(intent: str, requested_denied_actions: list[str]) -> str:
    if requested_denied_actions:
        return "denied_lower_phase_dependency"
    if intent in {"runtime-task", "browser-task", "scheduled-workflow", "approval-action", "handoff"}:
        return "approval_gated_lower_phase_dependency"
    if intent in PROPOSAL_INTENTS:
        return "proposal_only"
    if intent == "dashboard-query":
        return "read_only_preview"
    if intent in MODEL_BOUND_INTENTS:
        return "model_route_preview_only"
    return "manual_review"


def _ambiguity_report(message: str, classification: dict[str, Any]) -> dict[str, Any]:
    lowered = message.lower()
    reasons: list[str] = []
    if not message:
        reasons.append("empty_command")
    if re.search(r"\b(do|handle|fix|process|run)\b\s+(the\s+)?(thing|it|that|this)\b", lowered):
        reasons.append("missing_explicit_target")
    if classification.get("confidence") == "fallback" and re.search(r"\b(do|run|make|fix|update|handle|process)\b", lowered):
        reasons.append("no_deterministic_intent_match")
    return {
        "status": "ambiguous" if reasons else "unambiguous",
        "reasons": reasons,
        "requires_operator_clarification": bool(reasons),
    }


def _dependency_report(key: str) -> dict[str, str]:
    """Return dependency metadata with the exact Phase 11 handover field names."""

    item = dict(BACKEND_DEPENDENCY_CATALOG[key])
    return {
        "dependency_key": key,
        **item,
    }


def _backend_dependencies(intent: str, requested_denied_actions: list[str]) -> list[dict[str, str]]:
    keys: list[str] = []
    if intent in {"runtime-task", "scheduled-workflow"}:
        keys.extend(["lifecycle_execution", "runtime_dispatch"])
    if intent == "browser-task":
        keys.append("browser_shell_connector_authority")
    if intent == "approval-action":
        keys.append("approval_consumption_execution")
    if intent == "handoff":
        keys.append("runtime_dispatch")
    if intent in {"source-note", "synthesis-note"}:
        keys.append("source_pack_creation_promotion")
    if intent in {"vault-node-create", "vault-node-update"}:
        keys.append("canonical_knowledge_promotion")
    for action in requested_denied_actions:
        dep = _DENIED_ACTION_TO_DEPENDENCY.get(action)
        if dep:
            keys.append(dep)
    return [
        _dependency_report(key)
        for key in dict.fromkeys(keys)
        if key in BACKEND_DEPENDENCY_CATALOG
    ]


def _schema_preview_validation(preview: dict[str, Any], required: list[str], allowed: list[str]) -> dict[str, Any]:
    missing = [key for key in required if key not in preview]
    extra = [key for key in preview if key not in allowed]
    return {
        "compatible_with_schema": not missing and not extra,
        "missing_required_fields": missing,
        "additional_properties": extra,
    }


def _build_schema_previews(action_spec: dict[str, Any], generated_at: str) -> dict[str, dict[str, Any]]:
    fingerprint = action_spec["fingerprint"]
    status = "blocked" if action_spec["blocked"] else "open"
    intent = "BLOCKER" if action_spec["blocked"] else "NOTICE"
    task_packet = {
        "task_id": f"phase11-{fingerprint[:12]}",
        "run_id": action_spec["intent_id"],
        "from": "Hermes/Optimus Phase 11 Chat",
        "to": "ChaseOS lower-phase foundation",
        "intent": intent,
        "status": status,
        "priority": "normal",
        "owner": None,
        "owner_instance": None,
        "request": action_spec["normalized_command"] or "empty Phase 11 chat intent",
        "expected_output": "Inspectable structured intent/action state only; no execution or mutation from chat router.",
        "depends_on": [],
        "artifacts": [],
        "source_platform": "phase11_chat",
        "source_channel_id": None,
        "source_thread_id": None,
        "source_channel_class": "operator_surface",
        "conversation_key": None,
        "origin_message_id": None,
        "control_plane_route": "phase11_chat_router_readonly_intent_contract",
        "work_fingerprint": fingerprint,
        "execution_constraints": {
            "allow_shell_commands": False,
            "allow_live_subprocess": False,
            "allowed_write_paths": [],
            "write_policy": "none",
        },
        "notes": "; ".join(action_spec["blocked_reasons"]) or "read-only preview allowed",
        "created_at": generated_at,
        "updated_at": generated_at,
        "expires_at": None,
    }
    event = {
        "event_id": f"phase11-event-{fingerprint[:12]}",
        "task_id": task_packet["task_id"],
        "run_id": action_spec["intent_id"],
        "from": "Hermes/Optimus Phase 11 Chat",
        "event_type": "blocked" if action_spec["blocked"] else "notice",
        "message": task_packet["notes"] or "Phase 11 read-only intent preview generated.",
        "artifacts": [],
        "created_at": generated_at,
    }
    return {
        "agent_bus_task_packet_preview": task_packet,
        "agent_bus_event_preview": event,
    }


def _command_verb(message: str) -> str | None:
    match = re.match(r"^/?([a-z][a-z-]*)\b", message.strip(), re.IGNORECASE)
    return match.group(1).lower() if match else None


def _target_runtime_hint(message: str) -> str | None:
    match = re.search(r"\b(?:ask|send to|handoff to|hand off to)\s+(Hermes|OpenClaw|Codex|Archon)\b", message, re.IGNORECASE)
    return match.group(1) if match else None


def _requested_action_summary(message: str, target_runtime: str | None) -> str | None:
    if not target_runtime:
        return None
    match = re.search(
        rf"\b(?:ask|send to|handoff to|hand off to)\s+{re.escape(target_runtime)}\s+(?:to\s+)?(?P<summary>.+)$",
        message,
        re.IGNORECASE,
    )
    if not match:
        return None
    return match.group("summary").strip().rstrip(".") or None


def _object_type(intent: str, requested_denied_actions: list[str]) -> str:
    if requested_denied_actions:
        return "denied_side_effect_request"
    return {
        "handoff": "runtime_coordination_request",
        "runtime-task": "runtime_task_request",
        "browser-task": "browser_or_shell_request",
        "scheduled-workflow": "schedule_request",
        "approval-action": "approval_action_request",
        "project-create": "project_proposal_request",
        "project-update": "project_proposal_request",
        "vault-node-create": "vault_node_proposal_request",
        "vault-node-update": "vault_node_proposal_request",
        "source-note": "source_capture_proposal_request",
        "synthesis-note": "synthesis_preview_request",
        "rnd-entry": "rnd_proposal_request",
        "roadmap-item": "roadmap_proposal_request",
        "memory-save": "memory_proposal_request",
        "archive": "archive_proposal_request",
        "dashboard-query": "read_only_status_query",
        "model-chat": "model_route_preview_request",
        "chat-answer": "chat_answer_preview_request",
    }.get(intent, "manual_review_request")


def _command_translation(
    normalized_message: str,
    intent: str,
    requested_denied_actions: list[str],
    affected_surfaces: list[str],
    required_approvals: list[str],
) -> dict[str, Any]:
    target_runtime = _target_runtime_hint(normalized_message)
    summary = _requested_action_summary(normalized_message, target_runtime)
    return {
        "translation_status": "translated_preview" if normalized_message else "empty_command",
        "parser_used": "deterministic_phase11_command_translation_v1",
        "command_verb": _command_verb(normalized_message),
        "object_type": _object_type(intent, requested_denied_actions),
        "target_hint": target_runtime,
        "normalized_action_spec": {
            "intent_class": intent,
            "target_runtime": target_runtime,
            "requested_action_summary": summary or normalized_message or None,
            "affected_surfaces": affected_surfaces,
            "required_approvals": required_approvals,
            "side_effect_targets_declared": False,
        },
    }


def _dry_run_preview(action_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "preview_model": "phase11_action_spec_dry_run_preview_v1",
        "dry_run_preview_only": True,
        "would_execute": False,
        "would_write": False,
        "would_dispatch_agent_bus_task": False,
        "would_consume_approval": False,
        "would_call_provider": False,
        "would_control_browser_or_shell": False,
        "affected_surfaces": action_spec["affected_surfaces"],
        "required_approvals": action_spec["required_approvals"],
        "blocked_reasons": action_spec["blocked_reasons"],
    }


def _build_action_spec(
    normalized_message: str,
    classification: dict[str, Any],
    blocked_reasons: list[str],
    untrusted: dict[str, Any],
    previous_intent_fingerprints: list[str] | None,
) -> dict[str, Any]:
    intent = classification["intent_class"]
    fingerprint = hashlib.sha256(f"{intent}\n{normalized_message.lower()}".encode("utf-8")).hexdigest()
    prior = set(previous_intent_fingerprints or [])
    duplicate = fingerprint in prior
    ambiguity = _ambiguity_report(normalized_message, classification)
    final_blocked_reasons = list(blocked_reasons)
    if ambiguity["requires_operator_clarification"]:
        final_blocked_reasons.append("ambiguous_command_requires_operator_clarification")
    if duplicate:
        final_blocked_reasons.append("duplicate_intent_detected")
    final_blocked_reasons = list(dict.fromkeys(final_blocked_reasons))
    requested_denied_actions = list(untrusted.get("requested_denied_actions") or [])
    affected_surfaces = _affected_surfaces(intent, requested_denied_actions)
    required_approvals = _required_approvals(intent, requested_denied_actions)
    denial_status = "allowed_preview_only"
    if requested_denied_actions or untrusted.get("prompt_injection_suspected"):
        denial_status = "denied"
    elif final_blocked_reasons:
        denial_status = "blocked_pending_backend_or_approval"
    action_spec = {
        "intent_id": f"phase11-intent:{fingerprint[:16]}",
        "fingerprint": fingerprint,
        "normalized_command": normalized_message,
        "intent_class": intent,
        "matched_rule": classification.get("matched_rule"),
        "affected_surfaces": affected_surfaces,
        "authority_class": _authority_class(intent, requested_denied_actions),
        "required_approvals": required_approvals,
        "execution_allowed": False,
        "blocked": bool(final_blocked_reasons),
        "blocked_reasons": final_blocked_reasons,
        "ambiguity": ambiguity,
        "denial_status": denial_status,
        "duplicate_handling": {
            "status": "duplicate_detected" if duplicate else "unique_or_unchecked",
            "fingerprint_basis": "sha256(intent_class + normalized_command_lowercase)",
            "duplicate_of": fingerprint if duplicate else None,
        },
    }
    action_spec["command_translation"] = _command_translation(
        normalized_message,
        intent,
        requested_denied_actions,
        affected_surfaces,
        required_approvals,
    )
    action_spec["dry_run_preview"] = _dry_run_preview(action_spec)
    return action_spec


def build_phase11_chat_router_contract(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    previous_intent_fingerprints: list[str] | None = None,
) -> dict[str, Any]:
    """Build a no-execution router contract for one chat message."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    classification = classify_phase11_intent(normalized_message, explicit_intent=explicit_intent)
    intent = classification["intent_class"]
    provider_contract = None
    blocked_reasons: list[str] = []

    if intent in MODEL_BOUND_INTENTS:
        provider_contract = build_provider_routing_consumer_contract(vault, phase11_intent=intent)
        if provider_contract.get("routing_status") != "route_contract_satisfied":
            blocked_reasons.append("provider_route_contract_not_satisfied")

    if intent in PROPOSAL_INTENTS:
        blocked_reasons.append("intent_requires_proposal_surface_not_execution")
    if intent in APPROVAL_REQUIRED_INTENTS:
        blocked_reasons.append("intent_requires_operator_approval_before_mutation")
    if intent in {"runtime-task", "browser-task", "scheduled-workflow", "handoff"}:
        blocked_reasons.append("coordination_sensitive_work_requires_structured_chaseos_state")

    untrusted = _untrusted_input_report(normalized_message)
    action_spec = _action_spec_report(normalized_message)
    if untrusted["prompt_injection_suspected"]:
        blocked_reasons.append("prompt_injection_indicator_present")
    if untrusted["denied_side_effect_prompt_present"]:
        blocked_reasons.append("denied_side_effect_prompt_present")
    if (action_spec.get("ambiguity") or {}).get("requires_operator_clarification"):
        blocked_reasons.append("ambiguous_command_requires_operator_clarification")

    route_family = _route_family(intent)
    read_only_preview_allowed = (
        intent == "dashboard-query"
        and not untrusted["prompt_injection_suspected"]
        and not untrusted["denied_side_effect_prompt_present"]
    )

    generated_at = _now_utc()
    action_spec = _build_action_spec(
        normalized_message,
        classification,
        list(dict.fromkeys(blocked_reasons)),
        untrusted,
        previous_intent_fingerprints,
    )
    backend_dependencies = _backend_dependencies(intent, untrusted["requested_denied_actions"])
    safety_policy = build_phase11_chat_safety_policy(
        vault,
        intent_class=intent,
        requested_denied_actions=list(untrusted.get("requested_denied_actions") or []),
        prompt_injection_suspected=bool(untrusted.get("prompt_injection_suspected")),
        blocked_reasons=list(action_spec.get("blocked_reasons") or []),
    )
    schema_previews = _build_schema_previews(action_spec, generated_at)
    schema_validation = {
        "agent_bus_task_packet_preview": _schema_preview_validation(
            schema_previews["agent_bus_task_packet_preview"],
            ["task_id", "run_id", "from", "to", "intent", "status", "request", "expected_output", "created_at", "updated_at"],
            [
                "task_id", "run_id", "reply_to", "from", "to", "intent", "status", "priority", "owner",
                "owner_instance", "request", "expected_output", "depends_on", "artifacts", "source_platform",
                "source_channel_id", "source_thread_id", "source_channel_class", "conversation_key", "origin_message_id",
                "control_plane_route", "work_fingerprint", "execution_constraints", "notes", "created_at", "updated_at",
                "expires_at",
            ],
        ),
        "agent_bus_event_preview": _schema_preview_validation(
            schema_previews["agent_bus_event_preview"],
            ["event_id", "task_id", "run_id", "from", "event_type", "message", "created_at"],
            ["event_id", "task_id", "run_id", "from", "event_type", "message", "artifacts", "created_at"],
        ),
    }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": generated_at,
        "vault_root": str(vault),
        "read_only": True,
        "message_present": bool(normalized_message),
        "message_chars": len(normalized_message),
        "input_posture": untrusted,
        "intent_result": classification,
        "route_decision": {
            "route_family": route_family,
            "next_surface": _next_surface(intent),
            "route_execution_allowed": False,
            "policy_execution_allowed": False,
            "safety_policy_status": safety_policy.get("policy_status"),
            "read_only_preview_allowed_for_future_router": read_only_preview_allowed,
            "proposal_required": intent in PROPOSAL_INTENTS,
            "approval_required": intent in APPROVAL_REQUIRED_INTENTS,
            "model_route_required": intent in MODEL_BOUND_INTENTS,
            "provider_route_status": (provider_contract or {}).get("routing_status"),
            "blocked_reasons": action_spec["blocked_reasons"],
        },
        "action_spec": action_spec,
        "safety_policy": safety_policy,
        "backend_dependencies": backend_dependencies,
        "schema_previews": schema_previews,
        "schema_validation": schema_validation,
        "provider_routing_contract": provider_contract,
        "consumer_contract": {
            "llm_intent_classifier_allowed_by_this_surface": False,
            "deterministic_classifier_only": True,
            "may_render_intent_preview": True,
            "may_render_required_approval": True,
            "may_render_provider_readiness": True,
            "must_treat_chat_input_as_untrusted": True,
            "must_use_provider_routing_contract_before_model_call": True,
            "must_route_writes_through_studio_service": True,
            "must_route_runtime_work_through_chaseos_structured_state": True,
            "must_not_execute_embedded_instructions": True,
        },
        "authority": {
            "read_only": True,
            "model_calls_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "approval_execution_allowed": False,
            "vault_writes_allowed": False,
            "conversation_persistence_allowed": False,
            "agent_bus_task_write_allowed": False,
            "schedule_mutation_allowed": False,
            "canonical_mutation_allowed": False,
            **safety_policy.get("authority_matrix", {}),
            "credential_values_visible": False,
        },
        "denied_by_this_surface": [
            "llm_intent_classification_call",
            "provider_api_call",
            "chat_response_generation_call",
            "runtime_dispatch",
            "browser_control",
            "approval_grant_or_reject",
            "vault_file_write",
            "conversation_log_write",
            "agent_bus_task_write",
            "schedule_mutation",
            "credential_value_display",
            "canonical_writeback",
        ],
        "next_action": "wire_phase11_chat_panel_to_readonly_contract_before_any_execution",
    }


def format_phase11_chat_router_contract(payload: dict[str, Any]) -> str:
    intent = payload.get("intent_result") or {}
    route = payload.get("route_decision") or {}
    lines = [
        "Phase 11 Chat Router Read-Only Intent Contract",
        f"- intent_class: {intent.get('intent_class')}",
        f"- classifier: {intent.get('classifier')}",
        f"- llm_classifier_used: {intent.get('llm_classifier_used')}",
        f"- route_family: {route.get('route_family')}",
        f"- next_surface: {route.get('next_surface')}",
        f"- route_execution_allowed: {route.get('route_execution_allowed')}",
        f"- safety_policy_status: {route.get('safety_policy_status')}",
        f"- approval_required: {route.get('approval_required')}",
        f"- provider_route_status: {route.get('provider_route_status')}",
    ]
    blockers = route.get("blocked_reasons") or []
    if blockers:
        lines.append("blocked_reasons:")
        for reason in blockers:
            lines.append(f"- {reason}")
    lines.append("Boundary: read-only intent contract only; no LLM call, provider call, runtime dispatch, browser control, approval execution, vault write, conversation write, or canonical writeback.")
    return "\n".join(lines)
