"""Static UI checks for runtime live-status and Chat/Home product surfaces."""

from __future__ import annotations

from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parent / "shell" / "frontend"


def test_command_center_has_fail_open_shell() -> None:
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    assert "commandCenterFallbackShell" in app
    assert "homeShell(defaultHomeState())" in app
    assert "The page remains usable for orientation while live records load" in app


def test_chat_product_surface_exposes_folders_and_previous_chats() -> None:
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    assert "Folders" in app
    assert "Previous chats" in app
    assert "phase11-chat-history-row" in app
    assert "Live Runtime Sync" in app
    assert "Connected" in app
    assert "Sync needed" in app
    assert "_renderChatRuntimeSyncPanel" in app
    assert "gateway_ports_checked" in app
    assert "runtime_can_receive_chat" in app
    assert "titledRuntime !== runtimeId" in app
    assert "_refreshVisibleChatPendingResults" in app
    assert "poll_chat_result(taskId)" in app


def test_daemon_ui_distinguishes_gateway_live_from_heartbeat_ready() -> None:
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    assert "_daemonRuntimeStatusLabel" in app
    assert "gateway live" in app
    assert "Heartbeat sync needed" in app
    assert "repair heartbeat" in app
    assert "coordination watch state is stale" in app
    assert "Sync" in app
    assert "Connect" in app
    assert "Chat Connect is the operator's explicit opt-in to runtime-owned replies" in app
    assert "start_runtime_daemon(_selectedChatAdapter, true, '')" in app
    assert "stop_runtime_daemon(_selectedChatAdapter, '')" in app
    assert "Awaiting stop approval" in app


def test_studio_boot_does_not_auto_launch_runtime_start_preferences() -> None:
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    boot_section = app.split("Promise.allSettled([panelRegistryReady", 1)[1].split(
        "setInterval(refreshRuntimeStatusPill", 1
    )[0]
    assert "apply_runtime_chaseos_start_preferences(false)" not in boot_section
    assert "_applyRuntimeGatewayControlsOnChaseOSStart()" not in boot_section
    assert "apply_runtime_chaseos_start_preferences(true)" in app


def test_runtime_gateway_only_status_has_css() -> None:
    css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")

    assert "pip--port-live" in css
    assert "daemon-degraded" in css
    assert "status--warning" in css
    assert "phase11-chat-history-row" in css
    assert "phase11-chat-runtime-sync-card" in css
    assert "phase11-chat-runtime-sync-grid" in css


def test_final_productization_visual_qa_mocks_live_chat_runtime_sync() -> None:
    qa = (Path(__file__).resolve().parent / "final_productization_visual_qa.py").read_text(encoding="utf-8")

    assert "get_chat_runtime_availability" in qa
    assert "runtime_by_adapter" in qa
    assert "dispatch_ready" in qa
    assert "gateway_port_listening" in qa
    assert "runtime_can_receive_chat" in qa
