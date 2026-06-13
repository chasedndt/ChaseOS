"""Native ChaseOS Studio Chat workspace/thread foundation.

This surface models the product shape the operator asked for: ChatGPT/Claude
style projects and folders, Discord-style channels and threads, and ChaseOS
runtime lanes for Hermes, OpenClaw, Codex, and future runtimes. It is a
read-only contract. It does not create conversations, create Discord threads,
write Agent Bus tasks, mutate schedules, call providers, or persist messages.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_native_state import load_native_chat_state
from runtime.studio.phase11_chat_thread_conversations import load_chat_thread_conversations
from runtime.studio.runtime_live_status import build_runtime_live_status


SURFACE_ID = "phase11_chat_workspaces_foundation"
MODEL_VERSION = "studio.phase11_chat_workspaces_foundation.v1"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-proposal-consumption"

RUNTIME_CHANNEL_BINDINGS: dict[str, list[str]] = {
    "OpenClaw": ["runtime_chat_openclaw", "alerts_openclaw", "debug_openclaw"],
    "Hermes": ["runtime_chat_hermes", "alerts_hermes", "debug_hermes"],
    "Codex": ["control_plane_routing", "approvals", "audit_writeback"],
}

PREFERRED_RUNTIMES: list[dict[str, Any]] = [
    {
        "runtime_id": "OpenClaw",
        "label": "OpenClaw",
        "lane_role": "autonomous runtime execution and board handoff",
        "default_task_types": ["runtime.handoff", "workflow.dispatch", "code.patch"],
    },
    {
        "runtime_id": "Hermes",
        "label": "Hermes",
        "lane_role": "operator companion, chat continuity, and context routing",
        "default_task_types": ["runtime.handoff", "repo.inspect", "operator.brief"],
    },
    {
        "runtime_id": "Codex",
        "label": "Codex",
        "lane_role": "bounded development worker and patch/test runtime",
        "default_task_types": ["repo.inspect", "code.patch", "test.run", "code.review"],
    },
]

WORKSPACE_TEMPLATES: list[dict[str, Any]] = [
    {
        "workspace_id": "runtime-ops",
        "label": "Runtime Ops",
        "workspace_kind": "runtime_control_project",
        "workspace_mode_hint": "runtime_agent_ops",
        "context_paths": [
            "06_AGENTS/Agent-Control-Plane.md",
            "06_AGENTS/Agent-Registry.md",
            "06_AGENTS/Backends-Supported.md",
            "06_AGENTS/Runtime-Navigation-Map.md",
            "runtime/agent_bus/",
            "runtime/adapters/",
            "runtime/schedules/",
            ".chaseos/discord_instance_bindings.yaml",
        ],
        "runtime_lanes": ["OpenClaw", "Hermes", "Codex"],
        "folder_ids": ["runtime-control", "boards", "approvals", "schedules"],
        "board_targets": ["openclaw-kanban", "hermes-thread-board", "codex-patch-queue"],
    },
    {
        "workspace_id": "ventureops",
        "label": "VentureOps",
        "workspace_kind": "mission_project",
        "workspace_mode_hint": "founder_venture",
        "context_paths": [
            "06_AGENTS/VentureOps-Mission-Mode.md",
            "06_AGENTS/VentureOps-Instance-Intelligence.md",
            "runtime/ventureops/",
            "07_LOGS/VentureOps-Missions/",
            "01_PROJECTS/",
        ],
        "runtime_lanes": ["OpenClaw", "Hermes", "Codex"],
        "folder_ids": ["missions", "client-evidence", "runtime-chat", "workflow-packs"],
        "board_targets": ["mission-kanban", "external-evidence-review", "workflow-evolution-review"],
    },
    {
        "workspace_id": "personal-operator",
        "label": "Personal Operator",
        "workspace_kind": "personal_operating_project",
        "workspace_mode_hint": "home",
        "context_paths": [
            "00_HOME/",
            "07_LOGS/Daily/",
            "07_LOGS/Operator-Briefs/",
            "runtime/schedules/",
            "06_AGENTS/Permission-Matrix.md",
        ],
        "runtime_lanes": ["Hermes", "OpenClaw"],
        "folder_ids": ["today", "briefs", "personal-context", "schedules"],
        "board_targets": ["today-board", "personal-followups", "operator-brief-queue"],
    },
    {
        "workspace_id": "source-intelligence",
        "label": "Source Intelligence",
        "workspace_kind": "research_workspace",
        "workspace_mode_hint": "source_intelligence",
        "context_paths": [
            "runtime/source_intelligence/",
            "03_RESOURCES/",
            "04_SOPS/",
            "06_AGENTS/Vault-Map.md",
        ],
        "runtime_lanes": ["Hermes", "Codex"],
        "folder_ids": ["sources", "retrieval", "outputs", "research-threads"],
        "board_targets": ["source-review", "retrieval-work", "output-drafts"],
    },
]

FOLDER_LABELS: dict[str, str] = {
    "runtime-control": "Runtime Control",
    "boards": "Boards",
    "approvals": "Approvals",
    "schedules": "Schedules",
    "missions": "Missions",
    "client-evidence": "Client Evidence",
    "runtime-chat": "Runtime Chat",
    "workflow-packs": "Workflow Packs",
    "today": "Today",
    "briefs": "Briefs",
    "personal-context": "Personal Context",
    "sources": "Sources",
    "retrieval": "Retrieval",
    "outputs": "Outputs",
    "research-threads": "Research Threads",
}

THREAD_TEMPLATES: list[dict[str, Any]] = [
    {
        "thread_id": "runtime-ops-openclaw-chat",
        "workspace_id": "runtime-ops",
        "folder_id": "runtime-control",
        "title": "OpenClaw Runtime Chat",
        "thread_kind": "runtime_chat_lane",
        "runtime_id": "OpenClaw",
        "transport_channel_key": "runtime_chat_openclaw",
        "context_paths": ["runtime/agent_bus/", "runtime/adapters/openclaw/", "06_AGENTS/OpenClaw-Runtime-Profile.md"],
        "proposal_targets": ["agent_bus_task_packet", "openclaw-kanban"],
    },
    {
        "thread_id": "runtime-ops-hermes-chat",
        "workspace_id": "runtime-ops",
        "folder_id": "runtime-control",
        "title": "Hermes Runtime Chat",
        "thread_kind": "runtime_chat_lane",
        "runtime_id": "Hermes",
        "transport_channel_key": "runtime_chat_hermes",
        "context_paths": ["runtime/agent_bus/", "runtime/adapters/hermes/", "06_AGENTS/Hermes-Runtime-Profile.md"],
        "proposal_targets": ["agent_bus_task_packet", "hermes-thread-board"],
    },
    {
        "thread_id": "runtime-ops-codex-patches",
        "workspace_id": "runtime-ops",
        "folder_id": "boards",
        "title": "Codex Patch Queue",
        "thread_kind": "runtime_board_lane",
        "runtime_id": "Codex",
        "transport_channel_key": "control_plane_routing",
        "context_paths": ["runtime/codex/capabilities.yaml", "runtime/adapters/codex/", "06_AGENTS/Codex-Runtime-Profile.md"],
        "proposal_targets": ["codex-patch-queue", "agent_bus_task_packet"],
    },
    {
        "thread_id": "runtime-ops-schedules",
        "workspace_id": "runtime-ops",
        "folder_id": "schedules",
        "title": "Cron and Schedule Requests",
        "thread_kind": "schedule_management_lane",
        "runtime_id": "",
        "transport_channel_key": "",
        "context_paths": ["runtime/schedules/", "07_LOGS/Operator-Briefs/"],
        "proposal_targets": ["schedule_approval_packet"],
    },
    {
        "thread_id": "ventureops-mission-control",
        "workspace_id": "ventureops",
        "folder_id": "missions",
        "title": "Mission Control",
        "thread_kind": "runtime_project_thread",
        "runtime_id": "OpenClaw",
        "transport_channel_key": "runtime_chat_openclaw",
        "context_paths": ["runtime/ventureops/", "07_LOGS/VentureOps-Missions/"],
        "proposal_targets": ["mission-kanban", "agent_bus_task_packet"],
    },
    {
        "thread_id": "ventureops-external-evidence",
        "workspace_id": "ventureops",
        "folder_id": "client-evidence",
        "title": "External Evidence Review",
        "thread_kind": "approval_review_thread",
        "runtime_id": "Codex",
        "transport_channel_key": "audit_writeback",
        "context_paths": ["runtime/ventureops/", "07_LOGS/VentureOps-Missions/"],
        "proposal_targets": ["external-evidence-review"],
    },
    {
        "thread_id": "personal-operator-today",
        "workspace_id": "personal-operator",
        "folder_id": "today",
        "title": "Today",
        "thread_kind": "operator_daily_thread",
        "runtime_id": "Hermes",
        "transport_channel_key": "runtime_chat_hermes",
        "context_paths": ["00_HOME/", "07_LOGS/Daily/", "07_LOGS/Operator-Briefs/"],
        "proposal_targets": ["today-board", "operator-brief-queue"],
    },
    {
        "thread_id": "source-intelligence-research",
        "workspace_id": "source-intelligence",
        "folder_id": "research-threads",
        "title": "Research Threads",
        "thread_kind": "source_intelligence_thread",
        "runtime_id": "Hermes",
        "transport_channel_key": "runtime_chat_hermes",
        "context_paths": ["runtime/source_intelligence/", "03_RESOURCES/"],
        "proposal_targets": ["source-review", "output-drafts"],
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path_status(vault: Path, rel_path: str) -> dict[str, Any]:
    path = vault / rel_path
    return {
        "path": rel_path,
        "exists": path.exists(),
        "private_config": rel_path.startswith(".chaseos/"),
        "values_visible": False,
    }


def _capability_snapshot(vault: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        from runtime.agent_bus.capabilities import load_all_capabilities

        caps = load_all_capabilities(vault)
    except Exception as exc:
        return {}, [f"runtime_capability_registry_unreadable:{type(exc).__name__}"]
    return caps, []


def _discord_validation(vault: Path) -> dict[str, Any]:
    try:
        from runtime.discord_bindings import build_discord_binding_validation

        payload = build_discord_binding_validation(vault)
    except Exception as exc:
        return {
            "ok": False,
            "status": "unavailable",
            "valid": False,
            "summary": {
                "active_runtime_ids": [],
                "bound_channel_names": [],
                "bound_channel_count": 0,
                "primary_channel_count": 0,
            },
            "blockers": [f"discord_binding_validation_unavailable:{type(exc).__name__}"],
            "warnings": [],
            "secret_values_visible": False,
            "ids_visible": False,
        }
    return payload


def _channel_bound(discord: dict[str, Any], channel_key: str) -> bool:
    if not channel_key:
        return False
    for item in discord.get("primary_channels") or []:
        if str(item.get("name") or "") == channel_key:
            return bool(item.get("bound"))
    return channel_key in set((discord.get("summary") or {}).get("bound_channel_names") or [])


def _runtime_catalog(vault: Path, discord: dict[str, Any]) -> list[dict[str, Any]]:
    caps, _capability_warnings = _capability_snapshot(vault)
    cap_by_bus = {str(cap.bus_name).lower(): cap for cap in caps.values()}
    active_discord = {str(item).lower() for item in (discord.get("summary") or {}).get("active_runtime_ids") or []}
    runtimes: list[dict[str, Any]] = []
    for template in PREFERRED_RUNTIMES:
        runtime_id = str(template["runtime_id"])
        cap = cap_by_bus.get(runtime_id.lower())
        handles = []
        if cap:
            handles = [
                {
                    "task_type": handle.task_type,
                    "priority": handle.priority,
                    "notes": handle.notes,
                }
                for handle in cap.handles
            ]
        channel_keys = RUNTIME_CHANNEL_BINDINGS.get(runtime_id, [])
        bound_channel_keys = [key for key in channel_keys if _channel_bound(discord, key)]
        runtime_registered = bool(cap)
        discord_active = runtime_id.lower() in active_discord
        adapter_id = "openclaw" if runtime_id.lower() == "openclaw" else (
            "hermes" if runtime_id.lower() == "hermes" else runtime_id.lower()
        )
        try:
            live_status = build_runtime_live_status(
                vault,
                adapter_id,
                probe_wsl_processes=False,
            )
        except Exception as exc:
            live_status = {
                "status": "unknown",
                "status_source": "live_status_unavailable",
                "coordination_state": f"live_status_error:{type(exc).__name__}",
                "heartbeat_online": False,
                "gateway_port_online": False,
                "dispatch_ready": False,
                "gateway_ports_checked": [],
            }
        status = "registered_and_transport_bound" if runtime_registered and bound_channel_keys else (
            "registered_no_bound_transport" if runtime_registered else (
                "transport_bound_unregistered" if bound_channel_keys or discord_active else "planned_or_unregistered"
            )
        )
        runtimes.append(
            {
                **template,
                "adapter_id": adapter_id,
                "registered_in_agent_bus": runtime_registered,
                "discord_active": discord_active,
                "status": (
                    "gateway_live_heartbeat_required"
                    if live_status.get("gateway_port_online") and not live_status.get("heartbeat_online")
                    else "live_agent_bus_heartbeat"
                    if live_status.get("heartbeat_online")
                    else status
                ),
                "registration_status": status,
                "live_status": live_status,
                "runtime_live": live_status.get("status") == "running",
                "dispatch_ready": bool(live_status.get("dispatch_ready")),
                "heartbeat_online": bool(live_status.get("heartbeat_online")),
                "gateway_port_online": bool(live_status.get("gateway_port_online")),
                "gateway_port_listening": live_status.get("gateway_port_listening"),
                "status_source": live_status.get("status_source"),
                "coordination_state": live_status.get("coordination_state"),
                "capability_handle_count": len(handles),
                "handles": handles,
                "channel_keys": channel_keys,
                "bound_channel_keys": bound_channel_keys,
                "channel_values_visible": False,
                "secret_values_visible": False,
                "task_write_allowed_now": False,
                "runtime_dispatch_allowed_now": False,
                "provider_calls_allowed_now": False,
            }
        )
    return runtimes


def _folder(
    folder_id: str,
    workspace: dict[str, Any],
    vault: Path,
    *,
    native_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workspace_paths = list((native_record or {}).get("context_paths") or workspace.get("context_paths") or [])
    return {
        "folder_id": folder_id,
        "label": (native_record or {}).get("label") or FOLDER_LABELS.get(folder_id, folder_id.replace("-", " ").title()),
        "workspace_id": workspace["workspace_id"],
        "native_state_persisted": bool(native_record),
        "state_record_path": (native_record or {}).get("state_record_path"),
        "source_proposal_id": (native_record or {}).get("source_proposal_id"),
        "source_proposal_digest": (native_record or {}).get("source_proposal_digest"),
        "context_path_count": len(workspace_paths),
        "context_paths": [_path_status(vault, path) for path in workspace_paths[:8]],
        "chat_can_write_context": False,
        "chat_can_mutate_folder": False,
    }


def _tabs(workspace: dict[str, Any]) -> list[dict[str, Any]]:
    base_tabs = [
        ("chat", "Chat"),
        ("threads", "Threads"),
        ("context", "Context"),
        ("boards", "Boards"),
        ("schedules", "Schedules"),
    ]
    return [
        {
            "tab_id": f"{workspace['workspace_id']}-{tab_id}",
            "label": label,
            "workspace_id": workspace["workspace_id"],
            "route_preview": f"#chat/{workspace['workspace_id']}/{tab_id}",
            "navigation_preview_only": True,
            "execution_allowed_now": False,
            "write_allowed_now": False,
        }
        for tab_id, label in base_tabs
    ]


def _merge_unique(values: list[str], additions: list[str]) -> list[str]:
    merged = list(values)
    for item in additions:
        if item and item not in merged:
            merged.append(item)
    return merged


def _workspace_templates_with_native(native_state: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {str(item["workspace_id"]): dict(item) for item in WORKSPACE_TEMPLATES}
    order = [str(item["workspace_id"]) for item in WORKSPACE_TEMPLATES]
    for record in native_state.get("workspaces") or []:
        workspace_id = str(record.get("workspace_id") or "").strip()
        if not workspace_id:
            continue
        existing = by_id.get(workspace_id)
        if existing:
            existing["label"] = record.get("label") or existing.get("label")
            existing["workspace_kind"] = record.get("workspace_kind") or existing.get("workspace_kind")
            existing["workspace_mode_hint"] = record.get("workspace_mode_hint") or existing.get("workspace_mode_hint")
            existing["context_paths"] = _merge_unique(
                list(existing.get("context_paths") or []),
                list(record.get("context_paths") or []),
            )
            existing["folder_ids"] = _merge_unique(
                list(existing.get("folder_ids") or []),
                list(record.get("folder_ids") or []),
            )
            existing["runtime_lanes"] = _merge_unique(
                list(existing.get("runtime_lanes") or []),
                list(record.get("runtime_lanes") or []),
            )
            existing["native_state_persisted"] = True
            existing["state_record_path"] = record.get("state_record_path")
        else:
            by_id[workspace_id] = {
                "workspace_id": workspace_id,
                "label": record.get("label") or workspace_id.replace("-", " ").title(),
                "workspace_kind": record.get("workspace_kind") or "operator_created_chat_workspace",
                "workspace_mode_hint": record.get("workspace_mode_hint") or "runtime_agent_ops",
                "context_paths": list(record.get("context_paths") or []),
                "runtime_lanes": list(record.get("runtime_lanes") or []),
                "folder_ids": list(record.get("folder_ids") or []),
                "board_targets": list(record.get("board_targets") or []),
                "native_state_persisted": True,
                "state_record_path": record.get("state_record_path"),
            }
            order.append(workspace_id)
    return [by_id[item] for item in order if item in by_id]


def _native_folder_map(native_state: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    mapped: dict[tuple[str, str], dict[str, Any]] = {}
    for record in native_state.get("folders") or []:
        workspace_id = str(record.get("workspace_id") or "")
        folder_id = str(record.get("folder_id") or "")
        if workspace_id and folder_id:
            mapped[(workspace_id, folder_id)] = record
    return mapped


def _thread_templates_with_native(native_state: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {str(item["thread_id"]): dict(item) for item in THREAD_TEMPLATES}
    order = [str(item["thread_id"]) for item in THREAD_TEMPLATES]
    for record in native_state.get("threads") or []:
        thread_id = str(record.get("thread_id") or "").strip()
        if not thread_id:
            continue
        by_id[thread_id] = {
            "thread_id": thread_id,
            "workspace_id": str(record.get("workspace_id") or ""),
            "folder_id": str(record.get("folder_id") or ""),
            "title": str(record.get("title") or thread_id.replace("-", " ").title()),
            "thread_kind": str(record.get("thread_kind") or "operator_created_runtime_thread"),
            "runtime_id": str(record.get("runtime_id") or ""),
            "transport_channel_key": str(record.get("transport_channel_key") or ""),
            "context_paths": list(record.get("context_paths") or []),
            "proposal_targets": list(record.get("proposal_targets") or ["native_chat_state"]),
            "native_state_persisted": True,
            "state_record_path": record.get("state_record_path"),
            "source_proposal_id": record.get("source_proposal_id"),
            "source_proposal_digest": record.get("source_proposal_digest"),
        }
        if thread_id not in order:
            order.append(thread_id)
    return [by_id[item] for item in order if item in by_id]


def _thread_templates_with_conversations(
    thread_templates: list[dict[str, Any]],
    conversation_state: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {str(item.get("thread_id") or ""): dict(item) for item in thread_templates}
    order = [str(item.get("thread_id") or "") for item in thread_templates if item.get("thread_id")]
    for conversation in conversation_state.get("conversations") or []:
        thread_id = str(conversation.get("thread_id") or "").strip()
        if not thread_id:
            continue
        runtime_value = str(conversation.get("runtime_label") or conversation.get("runtime_id") or "Hermes")
        if thread_id in by_id:
            by_id[thread_id]["folder_label"] = str(
                conversation.get("folder_label") or by_id[thread_id].get("folder_label") or by_id[thread_id].get("folder_id") or ""
            )
            by_id[thread_id]["title"] = str(conversation.get("title") or by_id[thread_id].get("title") or thread_id)
            by_id[thread_id]["local_conversation_thread"] = True
            by_id[thread_id]["state_record_path"] = conversation.get("state_record_path") or by_id[thread_id].get("state_record_path")
            continue
        by_id[thread_id] = {
            "thread_id": thread_id,
            "workspace_id": str(conversation.get("workspace_id") or "runtime-ops"),
            "folder_id": str(conversation.get("folder_id") or "runtime-control"),
            "folder_label": str(conversation.get("folder_label") or conversation.get("folder_id") or "Runtime Control"),
            "title": str(conversation.get("title") or thread_id.replace("-", " ").title()),
            "thread_kind": "local_saved_chat_thread",
            "runtime_id": runtime_value,
            "transport_channel_key": "",
            "context_paths": [],
            "proposal_targets": ["agent_bus_task_packet"],
            "native_state_persisted": True,
            "local_conversation_thread": True,
            "state_record_path": conversation.get("state_record_path"),
        }
        order.append(thread_id)
    return [by_id[item] for item in order if item in by_id]


def _thread_status(thread: dict[str, Any], runtime_by_id: dict[str, dict[str, Any]], discord: dict[str, Any]) -> str:
    runtime_id = str(thread.get("runtime_id") or "")
    runtime = runtime_by_id.get(runtime_id)
    channel_bound = _channel_bound(discord, str(thread.get("transport_channel_key") or ""))
    if thread.get("native_state_persisted"):
        return "persisted_native_runtime_write_blocked" if runtime_id else "persisted_native_write_blocked"
    if thread.get("thread_kind") == "schedule_management_lane":
        return "proposal_ready_schedule_write_blocked"
    if runtime and (runtime.get("registered_in_agent_bus") or channel_bound):
        return "preview_ready_runtime_write_blocked"
    if runtime_id:
        return "planned_missing_runtime_or_transport_binding"
    return "preview_ready_write_blocked"


def _thread(
    template: dict[str, Any],
    *,
    vault: Path,
    runtime_by_id: dict[str, dict[str, Any]],
    discord: dict[str, Any],
    current_route_state: dict[str, Any] | None = None,
    drafts_by_thread: dict[str, list[dict[str, Any]]] | None = None,
    conversations_by_thread: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    transport_key = str(template.get("transport_channel_key") or "")
    current_route_state = current_route_state or {}
    drafts_by_thread = drafts_by_thread or {}
    conversations_by_thread = conversations_by_thread or {}
    thread_id = str(template["thread_id"])
    thread_drafts = drafts_by_thread.get(thread_id, [])
    conversation = conversations_by_thread.get(thread_id) or {}
    conversation_messages = list(conversation.get("messages") or [])
    return {
        **template,
        "status": _thread_status(template, runtime_by_id, discord),
        "route_preview": f"#chat/{template['workspace_id']}/threads/{thread_id}",
        "native_thread_state": "persisted_native" if template.get("native_state_persisted") else "planned_not_persisted",
        "native_state_persisted": bool(template.get("native_state_persisted")),
        "state_record_path": template.get("state_record_path"),
        "source_proposal_id": template.get("source_proposal_id"),
        "source_proposal_digest": template.get("source_proposal_digest"),
        "selected_in_route_state": current_route_state.get("thread_id") == thread_id,
        "draft_count": len(thread_drafts),
        "latest_draft_id": (thread_drafts[-1].get("draft_id") if thread_drafts else None),
        "message_draft_state_persisted": bool(thread_drafts),
        "chat_transcript_persisted": bool(conversation),
        "conversation_state_persisted": bool(conversation),
        "conversation_persisted": bool(conversation),
        "conversation_state_path": conversation.get("state_record_path"),
        "conversation_session_id": conversation.get("session_id") or "",
        "message_count": int(conversation.get("message_count") or 0),
        "latest_message_at_utc": conversation.get("last_message_at_utc") or "",
        "latest_message_preview": conversation.get("latest_message_preview") or "",
        "conversation_messages": conversation_messages[-20:],
        "message_write_allowed_now": False,
        "context_paths": [_path_status(vault, path) for path in template.get("context_paths") or []],
        "transport_binding": {
            "transport": "discord" if transport_key else "native",
            "channel_key": transport_key or None,
            "bound": _channel_bound(discord, transport_key),
            "ids_visible": False,
            "values_visible": False,
            "discord_api_called": False,
            "thread_created": False,
        },
        "actions_allowed_now": {
            "open_native_preview": True,
            "create_thread": False,
            "send_message": False,
            "agent_bus_task_write": False,
            "runtime_board_write": False,
            "schedule_mutation": False,
            "approval_consumption": False,
            "provider_call": False,
            "canonical_mutation": False,
        },
    }


def _workspace(
    template: dict[str, Any],
    *,
    vault: Path,
    runtimes: list[dict[str, Any]],
    threads: list[dict[str, Any]],
    native_folders_by_key: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    runtime_by_id = {str(item["runtime_id"]): item for item in runtimes}
    workspace_threads = [thread for thread in threads if thread.get("workspace_id") == template["workspace_id"]]
    native_folders_by_key = native_folders_by_key or {}
    folder_ids = list(template.get("folder_ids") or [])
    for (workspace_id, folder_id), _record in native_folders_by_key.items():
        if workspace_id == template["workspace_id"] and folder_id not in folder_ids:
            folder_ids.append(folder_id)
    lane_cards = []
    for runtime_id in template.get("runtime_lanes") or []:
        runtime = runtime_by_id.get(str(runtime_id), {})
        lane_cards.append(
            {
                "runtime_id": runtime_id,
                "status": runtime.get("status", "planned_or_unregistered"),
                "registration_status": runtime.get("registration_status", "unknown"),
                "runtime_live": bool(runtime.get("runtime_live")),
                "dispatch_ready": bool(runtime.get("dispatch_ready")),
                "heartbeat_online": bool(runtime.get("heartbeat_online")),
                "gateway_port_online": bool(runtime.get("gateway_port_online")),
                "gateway_port_listening": runtime.get("gateway_port_listening"),
                "status_source": runtime.get("status_source"),
                "coordination_state": runtime.get("coordination_state"),
                "registered_in_agent_bus": bool(runtime.get("registered_in_agent_bus")),
                "bound_channel_keys": list(runtime.get("bound_channel_keys") or []),
                "channel_values_visible": False,
                "dispatch_allowed_now": False,
            }
        )
    return {
        **template,
        "status": (
            "persisted_native_preview_only"
            if template.get("native_state_persisted")
            else ("foundation_ready_preview_only" if workspace_threads else "planned")
        ),
        "route_preview": f"#chat/{template['workspace_id']}",
        "native_state_persisted": bool(template.get("native_state_persisted")),
        "state_record_path": template.get("state_record_path"),
        "context_paths": [_path_status(vault, path) for path in template.get("context_paths") or []],
        "folders": [
            _folder(folder_id, template, vault, native_record=native_folders_by_key.get((template["workspace_id"], folder_id)))
            for folder_id in folder_ids
        ],
        "tabs": _tabs(template),
        "runtime_lanes": lane_cards,
        "threads": workspace_threads,
        "thread_count": len(workspace_threads),
        "folder_count": len(folder_ids),
        "tab_count": 5,
        "chat_workspace_write_allowed_now": False,
        "chat_thread_create_allowed_now": False,
        "runtime_board_write_allowed_now": False,
        "schedule_mutation_allowed_now": False,
        "provider_call_allowed_now": False,
    }


def _proposal_actions() -> list[dict[str, Any]]:
    return [
        {
            "action_id": "quick_open_native_runtime_chat",
            "label": "Quick open native runtime chat",
            "status": "foundation_preview_rendered",
            "authority": "navigation_preview_only",
            "implemented_now": "rendered_contract_only",
            "writes_allowed_now": False,
            "next_required_pass": "studio-chat-route-state",
        },
        {
            "action_id": "create_chat_project_or_folder",
            "label": "Create chat project or folder",
            "status": "proposal_writer_and_consumption_executor_available_digest_required",
            "authority": "approval_required_proposal_record_only",
            "implemented_now": "approval_queue_packet_writer_and_consumption_executor",
            "writes_allowed_now": False,
            "next_required_pass": "studio-runtime-chat-workspace-target-state-executor",
        },
        {
            "action_id": "create_runtime_thread",
            "label": "Create runtime thread",
            "status": "proposal_writer_and_consumption_executor_available_digest_required",
            "authority": "approval_required_proposal_record_only",
            "implemented_now": "approval_queue_packet_writer_and_consumption_executor",
            "writes_allowed_now": False,
            "next_required_pass": "studio-runtime-chat-workspace-target-state-executor",
        },
        {
            "action_id": "send_to_runtime_board",
            "label": "Send to Hermes/OpenClaw/Codex board",
            "status": "runtime_board_handoff_proposal_available_digest_required",
            "authority": "approval_required_board_handoff_request_only",
            "implemented_now": "approval_queue_packet_writer_only",
            "writes_allowed_now": False,
            "next_required_pass": "studio-chat-schedule-proposal-packets",
        },
        {
            "action_id": "manage_cron_tasks",
            "label": "Manage cron and scheduled tasks",
            "status": "planned_requires_schedule_approval_packet",
            "authority": "approval_required_future_write",
            "implemented_now": "not_built",
            "writes_allowed_now": False,
            "next_required_pass": "studio-chat-schedule-proposal-packets",
        },
        {
            "action_id": "chat_driven_runtime_setup",
            "label": "Chat-driven runtime setup visible in Studio",
            "status": "planned_requires_setup_proposal_packet",
            "authority": "proposal_and_validation_only",
            "implemented_now": "not_built",
            "writes_allowed_now": False,
            "next_required_pass": "studio-chat-runtime-setup-proposals",
        },
    ]


def build_phase11_chat_workspaces_foundation(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
) -> dict[str, Any]:
    """Build a no-side-effect Chat workspace/thread foundation payload."""

    vault = Path(vault_root).resolve()
    discord = _discord_validation(vault)
    native_state = load_native_chat_state(vault)
    conversation_state = load_chat_thread_conversations(vault)
    conversations_by_thread = conversation_state.get("conversations_by_thread_id") or {}
    current_route_state = native_state.get("route_state") or {}
    drafts_by_thread: dict[str, list[dict[str, Any]]] = {}
    for draft in native_state.get("drafts") or []:
        thread_id = str(draft.get("thread_id") or "")
        if thread_id:
            drafts_by_thread.setdefault(thread_id, []).append(draft)
    caps, capability_warnings = _capability_snapshot(vault)
    runtimes = _runtime_catalog(vault, discord)
    runtime_by_id = {str(item["runtime_id"]): item for item in runtimes}
    workspace_templates = _workspace_templates_with_native(native_state)
    thread_templates = _thread_templates_with_conversations(
        _thread_templates_with_native(native_state),
        conversation_state,
    )
    native_folders_by_key = _native_folder_map(native_state)
    for folder in conversation_state.get("folders") or []:
        workspace_id = str(folder.get("workspace_id") or "")
        folder_id = str(folder.get("folder_id") or "")
        if workspace_id and folder_id:
            native_folders_by_key.setdefault((workspace_id, folder_id), folder)
    threads = [
        _thread(
            template,
            vault=vault,
            runtime_by_id=runtime_by_id,
            discord=discord,
            current_route_state=current_route_state,
            drafts_by_thread=drafts_by_thread,
            conversations_by_thread=conversations_by_thread,
        )
        for template in thread_templates
    ]
    workspaces = [
        _workspace(
            template,
            vault=vault,
            runtimes=runtimes,
            threads=threads,
            native_folders_by_key=native_folders_by_key,
        )
        for template in workspace_templates
    ]
    folders = [folder for workspace in workspaces for folder in workspace.get("folders") or []]
    tabs = [tab for workspace in workspaces for tab in workspace.get("tabs") or []]
    bound_channel_names = list((discord.get("summary") or {}).get("bound_channel_names") or [])
    warnings = list(capability_warnings)
    warnings.extend(discord.get("warnings") or [])
    if discord.get("status") != "valid":
        warnings.extend(discord.get("blockers") or [])

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "status": "PARTIAL / FOUNDATION / READ-ONLY PROPOSAL SURFACE",
        "summary": {
            "native_chat_project_model_ready": True,
            "workspace_count": len(workspaces),
            "folder_count": len(folders),
            "tab_count": len(tabs),
            "thread_count": len(threads),
            "native_state_record_count": native_state.get("record_count"),
            "native_state_workspace_count": native_state.get("workspace_count"),
            "native_state_folder_count": native_state.get("folder_count"),
            "native_state_thread_count": native_state.get("thread_count"),
            "route_state_persisted": native_state.get("route_state_persisted"),
            "draft_count": native_state.get("draft_count"),
            "conversation_count": (conversation_state.get("summary") or {}).get("conversation_count", 0),
            "conversation_message_count": (conversation_state.get("summary") or {}).get("message_count", 0),
            "local_ui_state_count": native_state.get("local_ui_state_count"),
            "runtime_lane_count": sum(len(workspace.get("runtime_lanes") or []) for workspace in workspaces),
            "registered_runtime_count": len(caps),
            "preferred_runtime_count": len(runtimes),
            "runtime_live_count": sum(1 for runtime in runtimes if runtime.get("runtime_live")),
            "runtime_gateway_live_count": sum(1 for runtime in runtimes if runtime.get("gateway_port_online")),
            "runtime_heartbeat_live_count": sum(1 for runtime in runtimes if runtime.get("heartbeat_online")),
            "discord_binding_status": discord.get("status"),
            "discord_bound_channel_count": len(bound_channel_names),
            "message_present": bool(str(message or "").strip()),
            "explicit_intent": explicit_intent or "",
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "native_navigation_model": {
            "route_family": "studio_chat_workspace_thread",
            "project_route_preview": "#chat/{workspace_id}",
            "thread_route_preview": "#chat/{workspace_id}/threads/{thread_id}",
            "tabs_route_preview": "#chat/{workspace_id}/{tab_id}",
            "navigation_preview_only": True,
            "route_state_persistence_built": True,
            "message_draft_state_persistence_built": True,
            "current_route_state": current_route_state,
            "native_state_read_model_built": True,
        },
        "transport_bridge": {
            "discord": {
                "source_config_path": ".chaseos/discord_instance_bindings.yaml",
                "example_template": "runtime/bindings/discord_instance_bindings.example.yaml",
                "setup_sop": "04_SOPS/Discord-Control-Plane-Setup-SOP.md",
                "status": discord.get("status"),
                "valid": bool(discord.get("valid")),
                "active_runtime_ids": list((discord.get("summary") or {}).get("active_runtime_ids") or []),
                "bound_channel_names": bound_channel_names,
                "ids_visible": False,
                "secret_values_visible": False,
                "discord_api_calls_performed": False,
                "thread_creation_performed": False,
                "webhook_calls_performed": False,
            },
            "native_studio": {
                "project_folder_thread_model_rendered": True,
                "native_state_root": native_state.get("state_root"),
                "native_state_record_count": native_state.get("record_count"),
                "route_state_persisted": native_state.get("route_state_persisted"),
                "draft_count": native_state.get("draft_count"),
                "conversation_store_written": False,
                "conversation_store_read_model_ready": True,
                "conversation_count": (conversation_state.get("summary") or {}).get("conversation_count", 0),
                "conversation_message_count": (conversation_state.get("summary") or {}).get("message_count", 0),
                "thread_store_written_by_this_surface": False,
                "board_store_written": False,
            },
        },
        "native_state": native_state,
        "conversation_state": conversation_state,
        "runtime_lanes": runtimes,
        "workspaces": workspaces,
        "folders": folders,
        "tabs": tabs,
        "threads": threads,
        "proposal_actions": _proposal_actions(),
        "authority": {
            "read_only": True,
            "chat_workspace_write_allowed": False,
            "chat_folder_write_allowed": False,
            "chat_thread_create_allowed": False,
            "chat_message_send_allowed": False,
            "conversation_persistence_allowed": False,
            "local_conversation_state_allowed": True,
            "discord_api_calls_allowed": False,
            "discord_thread_create_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_board_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "schedule_mutation_allowed": False,
            "approval_consumption_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "chat_workspace_write",
            "chat_folder_write",
            "chat_thread_create",
            "chat_message_send",
            "conversation_log_write",
            "discord_api_call",
            "discord_thread_create",
            "agent_bus_task_write",
            "runtime_board_write",
            "runtime_dispatch",
            "schedule_mutation",
            "approval_consumption",
            "provider_api_call",
            "credential_value_display",
            "canonical_writeback",
        ],
        "readiness": {
            "studio_runtime_chat_workspaces_foundation_ready": True,
            "native_chat_state_read_model_ready": True,
            "native_chat_state_record_count": native_state.get("record_count"),
            "native_chat_route_state_read_model_ready": True,
            "native_chat_draft_state_read_model_ready": True,
            "native_chat_conversation_read_model_ready": True,
            "native_chat_project_model_ready": True,
            "native_chat_folder_model_ready": True,
            "native_chat_tab_model_ready": True,
            "native_chat_thread_model_ready": True,
            "runtime_lanes_visible": True,
            "discord_transport_bridge_redacted": True,
            "native_thread_creation_blocked": True,
            "message_send_blocked": True,
            "agent_bus_task_write_blocked": True,
            "runtime_board_write_blocked": True,
            "schedule_mutation_blocked": True,
            "provider_call_blocked": True,
            "credential_values_hidden": True,
            "warnings": list(dict.fromkeys(warnings)),
            "blockers": [],
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }
