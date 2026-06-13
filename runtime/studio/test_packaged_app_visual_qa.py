"""Tests for packaged Studio app visual QA."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

import pytest

from runtime.studio import capture_markdown_packaged_action_clickthrough as clickthrough_cli
from runtime.studio import capture_markdown_packaged_open_safety as open_safety_cli
from runtime.studio import packaged_app_visual_qa as visual_qa


def _write_png(path: Path, width: int, height: int, pixels: list[bytes]) -> None:
    rows = []
    for row_index in range(height):
        start = row_index * width
        rows.append(b"\x00" + b"".join(pixels[start : start + width]))
    raw = zlib.compress(b"".join(rows))

    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", raw)
        + chunk(b"IEND", b"")
    )


def test_internal_qa_capture_rejects_blank_self_capture(tmp_path: Path) -> None:
    screenshot = tmp_path / "blank.png"
    meta = tmp_path / "blank.qa-meta.json"
    width = 320
    height = 220
    _write_png(screenshot, width, height, [b"\x00\x00\x00"] * width * height)
    screenshot.write_bytes(screenshot.read_bytes() + (b"x" * 2048))
    meta.write_text(
        json.dumps(
            {
                "ok": True,
                "method": "qscreen_grabwindow",
                "width": width,
                "height": height,
                "window_title": "ChaseOS Studio - test",
            }
        ),
        encoding="utf-8",
    )

    result = visual_qa._read_internal_qa_capture(meta, screenshot)

    assert result["ok"] is False
    assert result["error"] == "internal_qa_capture_blank_or_near_uniform"
    assert result["visual_verification"]["ok"] is False


def _write_capture_review_artifacts(
    output_path: Path,
    review_status: str = "reviewed",
    *,
    capture_method: str = "studio_manual_text",
    extraction_status: str = "complete",
    local_image_text: bool = False,
) -> None:
    content = output_path.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    review_state = {"new_status": review_status, "reviewed_by": "studio-operator"}
    local_text_metadata = (
        {
            "status": "text_extracted",
            "engine_id": "configured-command",
            "engine_protocol": "stdout_image_path",
            "extracted_text_sha256": "abc",
            "extracted_text_char_count": 42,
            "cloud_optical_character_recognition_allowed": False,
            "provider_call_allowed": False,
            "secret_scan_required_after_extraction": True,
        }
        if local_image_text
        else {}
    )
    attachment_review_policy = (
        {
            "ocr_status": "text_extracted",
            "runtime_delete_allowed": False,
        }
        if local_image_text
        else {}
    )
    output_path.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "content_filename": output_path.name,
                "content_sha256": content_hash,
                "review_status": review_status,
                "quarantine_status": review_status,
                "operator_review_state": review_state,
                "review_history": [review_state],
                "extra_metadata": {
                    "visual_capture": {
                        "method": capture_method,
                        "extraction_status": extraction_status,
                        "review_status": review_status,
                        "operator_review_state": review_state,
                        "local_optical_character_recognition": local_text_metadata,
                        "attachment_review_policy": attachment_review_policy,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    output_path.with_suffix(".visual_capture.json").write_text(
        json.dumps(
            {
                "routing": {
                    "review_status": review_status,
                    "operator_review_state": review_state,
                }
            }
        ),
        encoding="utf-8",
    )


class FakeProcess:
    def __init__(self, *, alive: bool = True, stdout: str = "", stderr: str = "") -> None:
        self.pid = 23456
        self.returncode = None
        self._alive = alive
        self._stdout = stdout
        self._stderr = stderr
        self.terminated = False
        self.killed = False

    def poll(self):
        return None if self._alive else self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self._alive = False
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self._alive = False
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode

    def communicate(self, timeout=None):
        return self._stdout, self._stderr


def test_hidden_powershell_runner_uses_no_window_creationflag(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeCompletedProcess:
        returncode = 0
        stdout = "{}"
        stderr = ""

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeCompletedProcess()

    monkeypatch.setattr(visual_qa.os, "name", "nt")
    monkeypatch.setattr(visual_qa.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(visual_qa.subprocess, "run", fake_run)

    result = visual_qa._run_hidden_powershell("$true", timeout=1.0)

    assert result.returncode == 0
    assert captured["args"] == [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "$true",
    ]
    kwargs = captured["kwargs"]
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 1.0
    assert kwargs["shell"] is False
    assert kwargs["creationflags"] == 0x08000000


def test_forbidden_child_process_assessment_flags_shell_descendants() -> None:
    result = visual_qa._assess_forbidden_child_processes(
        [
            {
                "ok": True,
                "label": "after-launch",
                "descendants": [
                    {
                        "process_id": 34567,
                        "parent_process_id": 23456,
                        "name": "powershell.exe",
                        "executable_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                        "command_line": "powershell.exe -NoProfile",
                    }
                ],
            }
        ],
        ("powershell.exe",),
    )

    assert result["ok"] is False
    assert result["reason"] == "forbidden-child-process-present"
    assert result["matches"][0]["name"] == "powershell.exe"


def test_pyinstaller_temp_cleanup_limit_covers_packaged_studio_trees() -> None:
    assert visual_qa.MAX_PYINSTALLER_TEMP_CLEANUP_ENTRIES >= 20_000


def test_forbidden_visible_copy_terms_cover_product_facing_regressions() -> None:
    result = visual_qa._assess_forbidden_visible_copy(
        {
            "ok": True,
            "ui_automation_text": (
                "Proof lane dry-run daemon Build Logs Logs / Audit not mounted Shell action --json remain visible"
            ),
        }
    )

    assert result["ok"] is False
    assert result["matches"] == [
        "proof",
        "dry-run",
        "daemon",
        "build logs",
        "logs / audit",
        "not mounted",
        "shell action",
        "--json",
    ]


def test_packaged_visual_qa_rejects_executable_outside_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.exe"
    outside.write_bytes(b"exe")

    with pytest.raises(ValueError):
        visual_qa.build_packaged_app_visual_qa(vault, executable_path=outside)


def test_packaged_visual_qa_rejects_screenshot_outside_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    exe = vault / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    outside_screenshot = tmp_path / "outside.png"

    with pytest.raises(ValueError):
        visual_qa.build_packaged_app_visual_qa(
            vault,
            executable_path=exe,
            screenshot_path=outside_screenshot,
        )


def test_packaged_visual_qa_blocks_when_capture_fails(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {"ok": False, "error": "window_handle_not_found"},
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        settle_seconds=0.1,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_packaged_app_visual_qa"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["window_capture_ok"]["ok"] is False
    assert checks["host_policy_allows_launch"]["ok"] is True
    assert checks["owned_process_terminated"]["ok"] is True
    assert "Native window capture failed: window_handle_not_found." in report["blockers"]
    assert report["next_recommended_pass"] == "pass10b-native-window-capture-diagnostic"


def test_packaged_visual_qa_blocks_for_forbidden_studio_child_process(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: fake_process.pid)
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_wait_for_internal_capture(_meta_path, screenshot_path, **_kwargs):
        pixels = [
            bytes(((x + y) % 256, (x * 2) % 256, (y * 3) % 256))
            for y in range(240)
            for x in range(320)
        ]
        _write_png(Path(screenshot_path), 320, 240, pixels)
        return {
            "ok": True,
            "method": "qt_widget_grab",
            "capture_method": "qt_widget_grab",
            "process_id": fake_process.pid,
            "width": 320,
            "height": 240,
            "window_title": "ChaseOS Studio",
            "ui_automation_text": "ChaseOS Studio home capture markdown",
        }

    monkeypatch.setattr(visual_qa, "_wait_for_internal_qa_capture", fake_wait_for_internal_capture)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {
            "ok": True,
            "method": "copy_from_screen",
            "capture_method": "copy_from_screen",
            "process_id": fake_process.pid,
            "width": 320,
            "height": 240,
            "window_title": "ChaseOS Studio",
            "ui_automation_text": "ChaseOS Studio home capture markdown",
            "size_bytes": Path(_kwargs["screenshot_path"]).stat().st_size,
        },
    )
    monkeypatch.setattr(
        visual_qa,
        "_windows_process_descendants",
        lambda _root_process_id, *, label: {
            "ok": True,
            "label": label,
            "descendants": [
                {
                    "process_id": 34567,
                    "parent_process_id": fake_process.pid,
                    "name": "powershell.exe",
                    "executable_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                    "command_line": "powershell.exe -NoProfile",
                }
            ],
            "descendant_count": 1,
        },
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        initial_hash="#/capture-markdown",
        forbidden_child_process_names=("powershell.exe",),
        exit_after_screenshot=False,
        post_capture_observation_seconds=0,
        settle_seconds=0.1,
    )

    assert report["ok"] is False
    assert report["process_safety"]["reason"] == "forbidden-child-process-present"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["no_forbidden_child_processes"]["ok"] is False
    assert any("forbidden child process" in blocker.lower() for blocker in report["blockers"])


def test_packaged_capture_markdown_open_safety_separates_visual_confirmation_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_visual_report(_vault, **kwargs):
        return {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "launch": {"started": True, "process_alive_before_capture": True},
            "termination": {"terminated": True},
            "process_safety": {
                "ok": True,
                "reason": "no-forbidden-child-processes",
                "completed_scan_count": 1,
                "snapshot_count": 1,
                "matches": [],
            },
            "screenshot": {"path": str(kwargs.get("screenshot_path"))},
            "checks": [],
            "blockers": ["Native window capture failed: window_handle_not_found."],
        }

    monkeypatch.setattr(visual_qa, "build_packaged_app_visual_qa", fake_visual_report)

    report = visual_qa.build_packaged_capture_markdown_open_safety_proof(
        tmp_path,
        screenshot_root=tmp_path / "evidence",
    )

    assert report["ok"] is True
    assert report["blockers"] == []
    assert report["visual_confirmation"]["ok"] is False
    assert report["routes"][0]["visual_blockers"] == ["Native window capture failed: window_handle_not_found."]


def test_capture_markdown_action_script_targets_real_capture_controls() -> None:
    payload = visual_qa._capture_markdown_action_payload("unit-token")

    script = visual_qa._build_capture_markdown_action_script(payload)

    assert "capture-markdown-source-options" in script
    assert "data-capture-source-option=\"studio_shortcuts\"" in script
    assert "settings-capture-hotkeys" in script
    assert "'run_screen_capture_collector'" in script
    assert "'run_clipboard_text_collector'" in script
    assert "'active_browser_artifact_capture'" in script
    assert "'run_browser_artifact_collector'" in script
    assert "'chaseos_browser_page_capture'" in script
    assert "'run_chaseos_browser_page_collector'" in script
    assert "'discord_capture'" in script
    assert "'run_discord_artifact_collector'" in script
    assert "data-capture-hotkey-action=\"capture_screenshot\"" in script
    assert "new KeyboardEvent('keydown'" in script
    assert "__CHASEOS_CAPTURE_MARKDOWN_PROOF__" in script
    assert "allow_secret_redaction" in script
    assert "capture-markdown-title-input" in script
    assert "capture-markdown-preview-btn" in script
    assert "capture-markdown-save-btn" in script
    assert "capture-markdown-review-btn" in script
    assert "capture-markdown-review-note" in script
    assert "capture-markdown-approval-preview-btn" in script
    assert "capture-markdown-source-pack-write-btn" in script
    assert "capture-markdown-source-pack-aor-readiness-btn" in script
    assert "capture-markdown-source-pack-agent-bus-full-dispatch-btn" in script
    assert "capture-markdown-source-pack-sic-ingestion-btn" in script
    assert "source_intelligence_core_ingestion_button_dataset" in script
    assert "source_intelligence_core_ingestion_missing_dataset_keys" in script
    assert "packaged_capture_async_error" in script
    assert "capture-markdown-source-pack-sic-graph-indexing-btn" in script
    assert "capture-markdown-source-pack-canonical-promotion-btn" in script
    assert "capture-markdown-action-msg" in script
    assert "window.__CHASEOS_PACKAGED_CAPTURE_ACTION_RESULT__" in script
    assert payload["review_note"] in script
    assert payload["title"] in script


def test_capture_markdown_clickthrough_parser_supports_single_downstream_failure_case() -> None:
    args = clickthrough_cli.build_parser().parse_args(
        [
            "--capture-mode",
            "manual_text_downstream_failure",
            "--downstream-failure-case",
            "canonical_promotion_approval_request_bad_statement",
        ]
    )

    assert args.capture_mode == "manual_text_downstream_failure"
    assert args.downstream_failure_case == "canonical_promotion_approval_request_bad_statement"


def test_capture_markdown_open_safety_parser_exposes_observation_window() -> None:
    args = open_safety_cli.build_parser().parse_args(
        [
            "--post-capture-observation-seconds",
            "3.5",
            "--write-evidence",
        ]
    )

    assert args.post_capture_observation_seconds == 3.5
    assert args.write_evidence is True


def test_capture_markdown_action_error_result_preserves_partial_evidence() -> None:
    script = visual_qa._build_capture_markdown_action_script(
        visual_qa._capture_markdown_action_payload("unit-token")
    )

    assert script.count("save_action_message: saveActionMessage") == 5
    assert script.count("review_proof_before: reviewProofBefore") == 5
    assert script.count("review_proof_after: reviewProofAfter") == 5


def test_capture_markdown_action_assessment_requires_expected_output_markdown(tmp_path: Path) -> None:
    payload = visual_qa._capture_markdown_action_payload("unit-token")
    output_path = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources" / "unit-token.md"
    output_path.parent.mkdir(parents=True)
    output_path.write_text(
        "\n".join(
            [
                f"# Capture to Markdown - {payload['title']}",
                payload["raw_text"],
                payload["source_url"],
            ]
        ),
        encoding="utf-8",
    )
    _write_capture_review_artifacts(output_path)

    result = visual_qa._assess_capture_markdown_action_output(
        tmp_path,
        action_result={
            "ok": True,
            "status": "reviewed",
            "save_action_message": "Saved to quarantine.",
            "action_message": "Review: reviewed.",
            "preview_text": payload["preview_marker"],
            "recent_text": f"{payload['title']} reviewed",
            "source_card_proof": {
                "required_present": True,
                "available_inputs_visible": True,
                "blocked_collectors_visible": True,
                "explicit_screen_collector_visible": True,
                "explicit_screen_collector_settings_gated": True,
                "explicit_clipboard_collector_visible": True,
                "explicit_clipboard_collector_settings_gated": True,
                "explicit_browser_artifact_collector_visible": True,
                "explicit_browser_artifact_collector_settings_gated": True,
                "explicit_chaseos_browser_page_collector_visible": True,
                "explicit_chaseos_browser_page_collector_settings_gated": True,
                "explicit_discord_artifact_collector_visible": True,
                "explicit_discord_artifact_collector_settings_gated": True,
                "downstream_consumers_visible": True,
                "manual_text_selects_source_mode": True,
            },
            "release_readiness_proof": {
                "visible": True,
                "status": "partial_core_verified_optional_collectors_blocked",
                "ready_now_visible": True,
                "release_distribution_visible": True,
                "approval_gated_downstream_visible": True,
                "blocked_collectors_visible": True,
                "release_proof_open_visible": True,
                "full_language_visible": True,
                "public_signing_status_visible": True,
                "real_engine_gap_visible": True,
                "text": "Source Intelligence Core Agent Orchestration Runtime Public certificate-authority signing Public signing handoff Real image text engine quality Unverified on this host",
            },
            "shortcut_proof": {
                "settings_section_visible": True,
                "required_rows_present": True,
                "default_open_chord_visible": True,
                "default_focus_chord_visible": True,
                "collector_shortcut_rows_visible": True,
                "collector_shortcut_rows_configurable": True,
                "shortcut_input_capture_ok": True,
                "blocked_shortcut_disabled": True,
                "studio_shortcut_navigation_ok": True,
            },
            "review_proof_before": {
                "title_visible": True,
                "review_controls_visible": True,
                "review_path_present": True,
                "item_text": payload["title"],
            },
            "review_proof_after": {
                "selected_decision": "reviewed",
                "item_text": f"{payload['title']} reviewed",
            },
            "source_pack_proof": {
                "preview_visible": True,
                "write_button_visible": True,
                "write_button_enabled": True,
                "write_result_visible": True,
                "boundary_visible": True,
                "downstream_boundary_visible": True,
                "aor_readiness_result_visible": True,
                "aor_approval_design_button_visible": True,
                "aor_approval_consumption_result_visible": True,
                "agent_bus_task_result_visible": True,
                "aor_full_dispatch_result_visible": True,
                "source_intelligence_core_ingestion_result_visible": True,
                "graph_indexing_result_visible": True,
                "canonical_promotion_result_visible": True,
                "full_downstream_chain_visible": True,
                "source_pack_written_paths": [
                    "runtime/acquisition/packs/unit-token/exact_once_marker.json",
                    "runtime/acquisition/packs/unit-token/normalized_source_pack.json",
                    "runtime/acquisition/packs/unit-token/briefing_ready_input_set.json",
                ],
                "written_paths": [
                    "runtime/acquisition/packs/unit-token/exact_once_marker.json",
                    "runtime/acquisition/packs/unit-token/normalized_source_pack.json",
                    "runtime/acquisition/packs/unit-token/briefing_ready_input_set.json",
                    "runtime/studio/approvals/unit-token-aor-approval.json",
                    "runtime/studio/approvals/unit-token-source-intelligence-core-approval.json",
                    "07_LOGS/Promotion-Records/unit-token-canonical-promotion.json",
                ],
                "text": (
                    "Source-Pack Write Agent Orchestration Runtime dispatch "
                    "Source Intelligence Core Ingestion Graph Indexing Canonical Promotion"
                ),
            },
        },
        markdown_delta={
            "added": ["03_INPUTS/00_QUARANTINE/Sources/unit-token.md"],
            "removed": [],
            "modified": [],
        },
        approval_delta={
            "added": [
                "runtime/studio/approvals/unit-token-aor-approval.json",
                "runtime/studio/approvals/unit-token-source-intelligence-core-approval.json",
                "07_LOGS/Promotion-Records/unit-token-canonical-promotion.json",
            ],
            "removed": [],
            "modified": [],
        },
        source_pack_delta={
            "added": [
                "runtime/acquisition/packs/unit-token/exact_once_marker.json",
                "runtime/acquisition/packs/unit-token/normalized_source_pack.json",
                "runtime/acquisition/packs/unit-token/briefing_ready_input_set.json",
            ],
            "removed": [],
            "modified": [],
        },
        payload=payload,
    )

    assert result["ok"] is True
    assert result["output_markdown_paths"] == ["03_INPUTS/00_QUARANTINE/Sources/unit-token.md"]
    assert result["source_pack_artifact_delta"]["added"][0].startswith("runtime/acquisition/packs/")

    unrelated_delta = visual_qa._assess_capture_markdown_action_output(
        tmp_path,
        action_result={
            "ok": True,
            "status": "reviewed",
            "save_action_message": "Saved to quarantine.",
            "action_message": "Review: reviewed.",
            "preview_text": payload["preview_marker"],
            "recent_text": f"{payload['title']} reviewed",
            "source_card_proof": {
                "required_present": True,
                "available_inputs_visible": True,
                "blocked_collectors_visible": True,
                "explicit_screen_collector_visible": True,
                "explicit_screen_collector_settings_gated": True,
                "explicit_clipboard_collector_visible": True,
                "explicit_clipboard_collector_settings_gated": True,
                "explicit_browser_artifact_collector_visible": True,
                "explicit_browser_artifact_collector_settings_gated": True,
                "explicit_chaseos_browser_page_collector_visible": True,
                "explicit_chaseos_browser_page_collector_settings_gated": True,
                "explicit_discord_artifact_collector_visible": True,
                "explicit_discord_artifact_collector_settings_gated": True,
                "downstream_consumers_visible": True,
                "manual_text_selects_source_mode": True,
            },
            "release_readiness_proof": {
                "visible": True,
                "status": "partial_core_verified_optional_collectors_blocked",
                "ready_now_visible": True,
                "release_distribution_visible": True,
                "approval_gated_downstream_visible": True,
                "blocked_collectors_visible": True,
                "release_proof_open_visible": True,
                "full_language_visible": True,
                "public_signing_status_visible": True,
                "real_engine_gap_visible": True,
                "text": "Source Intelligence Core Agent Orchestration Runtime Public certificate-authority signing Public signing handoff Real image text engine quality Unverified on this host",
            },
            "shortcut_proof": {
                "settings_section_visible": True,
                "required_rows_present": True,
                "default_open_chord_visible": True,
                "default_focus_chord_visible": True,
                "collector_shortcut_rows_visible": True,
                "collector_shortcut_rows_configurable": True,
                "shortcut_input_capture_ok": True,
                "blocked_shortcut_disabled": True,
                "studio_shortcut_navigation_ok": True,
            },
            "review_proof_before": {
                "title_visible": True,
                "review_controls_visible": True,
                "review_path_present": True,
                "item_text": payload["title"],
            },
            "review_proof_after": {
                "selected_decision": "reviewed",
                "item_text": f"{payload['title']} reviewed",
            },
            "source_pack_proof": {
                "preview_visible": True,
                "write_button_visible": True,
                "write_button_enabled": True,
                "write_result_visible": True,
                "boundary_visible": True,
                "downstream_boundary_visible": True,
                "aor_readiness_result_visible": True,
                "aor_approval_design_button_visible": True,
                "aor_approval_consumption_result_visible": True,
                "agent_bus_task_result_visible": True,
                "aor_full_dispatch_result_visible": True,
                "source_intelligence_core_ingestion_result_visible": True,
                "graph_indexing_result_visible": True,
                "canonical_promotion_result_visible": True,
                "full_downstream_chain_visible": True,
                "source_pack_written_paths": [
                    "runtime/acquisition/packs/unit-token/exact_once_marker.json",
                    "runtime/acquisition/packs/unit-token/normalized_source_pack.json",
                    "runtime/acquisition/packs/unit-token/briefing_ready_input_set.json",
                ],
                "written_paths": [
                    "runtime/acquisition/packs/unit-token/exact_once_marker.json",
                    "runtime/acquisition/packs/unit-token/normalized_source_pack.json",
                    "runtime/acquisition/packs/unit-token/briefing_ready_input_set.json",
                    "runtime/studio/approvals/unit-token-aor-approval.json",
                    "runtime/studio/approvals/unit-token-source-intelligence-core-approval.json",
                    "07_LOGS/Promotion-Records/unit-token-canonical-promotion.json",
                ],
                "text": (
                    "Source-Pack Write Agent Orchestration Runtime dispatch "
                    "Source Intelligence Core Ingestion Graph Indexing Canonical Promotion"
                ),
            },
        },
        markdown_delta={
            "added": ["03_INPUTS/00_QUARANTINE/Sources/unit-token.md"],
            "removed": [],
            "modified": ["06_AGENTS/Codex-Runtime-Profile.md"],
        },
        approval_delta={
            "added": [
                "runtime/studio/approvals/unit-token-aor-approval.json",
                "runtime/studio/approvals/unit-token-source-intelligence-core-approval.json",
                "07_LOGS/Promotion-Records/unit-token-canonical-promotion.json",
            ],
            "removed": [],
            "modified": [],
        },
        source_pack_delta={
            "added": [
                "runtime/acquisition/packs/unit-token/exact_once_marker.json",
                "runtime/acquisition/packs/unit-token/normalized_source_pack.json",
                "runtime/acquisition/packs/unit-token/briefing_ready_input_set.json",
            ],
            "removed": [],
            "modified": [],
        },
        payload=payload,
    )

    assert unrelated_delta["ok"] is True
    assert unrelated_delta["ignored_unrelated_markdown_delta"] == {
        "added": [],
        "removed": [],
        "modified": ["06_AGENTS/Codex-Runtime-Profile.md"],
    }
    unrelated_checks = {item["name"]: item for item in unrelated_delta["checks"]}
    assert unrelated_checks["exactly_one_quarantine_markdown_added"]["ok"] is True

    blocked = visual_qa._assess_capture_markdown_action_output(
        tmp_path,
        action_result={"ok": True, "status": "saved"},
        markdown_delta={"added": [], "removed": [], "modified": []},
        approval_delta={"added": [], "removed": [], "modified": []},
        source_pack_delta={"added": [], "removed": [], "modified": []},
        payload=payload,
    )

    assert blocked["ok"] is False
    assert any("exactly_one_quarantine_markdown_added" in item for item in blocked["blockers"])


def test_capture_markdown_action_script_starts_async_work_after_return() -> None:
    script = visual_qa._build_capture_markdown_action_script(
        visual_qa._capture_markdown_action_payload("unit-token")
    )

    assert "setTimeout(() =>" in script
    assert "status: 'started'" in script
    assert '"started";' in script
    assert script.find("setTimeout(() =>") < script.rfind('"started";')


def test_packaged_capture_markdown_action_clickthrough_accepts_expected_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    payload = visual_qa._capture_markdown_action_payload("unit-token")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: fake_process.pid)
    monkeypatch.setattr(
        visual_qa,
        "_terminate_packaged_process_tree",
        lambda *_args, **_kwargs: {"attempted": True, "terminated": True, "returncode": 0},
    )
    monkeypatch.setattr(
        visual_qa,
        "_cleanup_new_pyinstaller_temp_dirs",
        lambda *_args, **_kwargs: {"attempted": True, "deleted": [], "failed": [], "reason": "test"},
    )
    monkeypatch.setattr(visual_qa, "_analyze_png_nonblank_and_content_area_dotnet", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(_args, *, env, **_kwargs):
        plan = json.loads(Path(env[visual_qa.QA_BATCH_PLAN_PATH_ENV]).read_text(encoding="utf-8"))
        route = plan["routes"][0]
        assert route["script_wait_for_result"] is False
        assert route["capture_delay_ms"] == 120000
        screenshot = Path(route["screenshot_path"])
        meta_path = Path(route["meta_path"])
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        pixels = [
            bytes(((x + y) % 256, (x * 3) % 256, (y * 5) % 256))
            for y in range(240)
            for x in range(320)
        ]
        source_pack_paths = [
            "runtime/acquisition/packs/_vcmi_source_pack_write_markers/unit-token.json",
            "runtime/acquisition/packs/visual-capture-preview/unit-token/source_packet_001.json",
            "runtime/acquisition/packs/visual-capture-preview/unit-token/normalized_source_pack.json",
            "runtime/acquisition/packs/visual-capture-preview/unit-token/briefing_ready_input_set.json",
        ]
        approval_paths = [
            "runtime/studio/approvals/unit-token-aor-approval.json",
            "runtime/studio/approvals/unit-token-source-intelligence-core-approval.json",
            "07_LOGS/Promotion-Records/unit-token-canonical-promotion.json",
        ]
        _write_png(screenshot, 320, 240, pixels)
        meta_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "method": "qt_widget_grab",
                    "process_id": fake_process.pid,
                    "width": 320,
                    "height": 240,
                    "route_id": route["id"],
                    "route_hash": route["hash"],
                    "route_script": {
                        "start": {"ok": True, "result": {"ok": True, "started": True}},
                        "final": {
                            "ok": True,
                            "result": {
                                "ok": True,
                                "status": "reviewed",
                                "save_action_message": "Saved to quarantine.",
                                "action_message": "Review: reviewed.",
                                "preview_text": payload["preview_marker"],
                                "recent_text": f"{payload['title']} reviewed",
                                "source_card_proof": {
                                    "required_present": True,
                                    "available_inputs_visible": True,
                                    "blocked_collectors_visible": True,
                                    "explicit_screen_collector_visible": True,
                                    "explicit_screen_collector_settings_gated": True,
                                    "explicit_clipboard_collector_visible": True,
                                    "explicit_clipboard_collector_settings_gated": True,
                                    "explicit_browser_artifact_collector_visible": True,
                                    "explicit_browser_artifact_collector_settings_gated": True,
                                    "explicit_chaseos_browser_page_collector_visible": True,
                                    "explicit_chaseos_browser_page_collector_settings_gated": True,
                                    "explicit_discord_artifact_collector_visible": True,
                                    "explicit_discord_artifact_collector_settings_gated": True,
                                    "downstream_consumers_visible": True,
                                    "manual_text_selects_source_mode": True,
                                },
                                "release_readiness_proof": {
                                    "visible": True,
                                    "status": "partial_core_verified_optional_collectors_blocked",
                                    "ready_now_visible": True,
                                    "release_distribution_visible": True,
                                    "approval_gated_downstream_visible": True,
                                    "blocked_collectors_visible": True,
                                    "release_proof_open_visible": True,
                                    "full_language_visible": True,
                                    "public_signing_status_visible": True,
                                    "real_engine_gap_visible": True,
                                    "text": "Source Intelligence Core Agent Orchestration Runtime Public certificate-authority signing Public signing handoff Real image text engine quality Unverified on this host",
                                },
                                "shortcut_proof": {
                                    "settings_section_visible": True,
                                    "required_rows_present": True,
                                    "default_open_chord_visible": True,
                                    "default_focus_chord_visible": True,
                                    "collector_shortcut_rows_visible": True,
                                    "collector_shortcut_rows_configurable": True,
                                    "shortcut_input_capture_ok": True,
                                    "blocked_shortcut_disabled": True,
                                    "studio_shortcut_navigation_ok": True,
                                },
                                "review_proof_before": {
                                    "title_visible": True,
                                    "review_controls_visible": True,
                                    "review_path_present": True,
                                    "item_text": payload["title"],
                                },
                                "review_proof_after": {
                                    "selected_decision": "reviewed",
                                    "item_text": f"{payload['title']} reviewed",
                                },
                                "source_pack_proof": {
                                    "preview_visible": True,
                                    "write_button_visible": True,
                                    "write_button_enabled": True,
                                    "write_result_visible": True,
                                    "boundary_visible": True,
                                    "downstream_boundary_visible": True,
                                    "aor_readiness_result_visible": True,
                                    "aor_approval_design_button_visible": True,
                                    "aor_approval_consumption_result_visible": True,
                                    "agent_bus_task_result_visible": True,
                                    "aor_full_dispatch_result_visible": True,
                                    "source_intelligence_core_ingestion_result_visible": True,
                                    "graph_indexing_result_visible": True,
                                    "canonical_promotion_result_visible": True,
                                    "full_downstream_chain_visible": True,
                                    "write_message": "Written.",
                                    "source_pack_written_paths": source_pack_paths,
                                    "written_paths": source_pack_paths + approval_paths,
                                    "text": (
                                        "Source-Pack Write Agent Orchestration Runtime dispatch "
                                        "Source Intelligence Core Ingestion Graph Indexing Canonical Promotion"
                                    ),
                                },
                                "body_text": (
                                    f"{payload['saved_message']} {payload['review_message']} "
                                    f"{payload['preview_marker']} {payload['title']} reviewed "
                                    "Source-Pack Write Source Intelligence Core ingestion Canonical promotion not performed"
                                ),
                            },
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        result_path = Path(env[visual_qa.QA_BATCH_RESULT_PATH_ENV])
        result_path.write_text(
            json.dumps({"ok": True, "done": True, "captured_count": 1, "expected_count": 1, "results": []}),
            encoding="utf-8",
        )
        output_path = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources" / "unit-token.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    f"# Capture to Markdown - {payload['title']}",
                    payload["raw_text"],
                    payload["source_url"],
                ]
            ),
            encoding="utf-8",
        )
        _write_capture_review_artifacts(output_path)
        for rel_path in source_pack_paths:
            source_pack_path = tmp_path / rel_path
            source_pack_path.parent.mkdir(parents=True, exist_ok=True)
            source_pack_path.write_text("{}", encoding="utf-8")
        for rel_path in approval_paths:
            approval_path = tmp_path / rel_path
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            approval_path.write_text("{}", encoding="utf-8")
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)

    report = visual_qa.build_packaged_capture_markdown_action_clickthrough(
        tmp_path,
        executable_path=exe,
        screenshot_root=tmp_path / "evidence",
        settle_seconds=0.1,
        run_token="unit-token",
    )

    assert report["ok"] is True
    assert report["action_assessment"]["output_markdown_paths"] == [
        "03_INPUTS/00_QUARANTINE/Sources/unit-token.md"
    ]
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["exactly_one_quarantine_markdown_added"]["ok"] is True
    assert checks["visible_review_controls_for_saved_capture"]["ok"] is True
    assert checks["recent_capture_review_status_updated"]["ok"] is True
    assert checks["review_sidecar_updated_to_reviewed"]["ok"] is True
    assert checks["review_packet_updated_to_reviewed"]["ok"] is True
    assert checks["source_pack_write_result_card_visible"]["ok"] is True
    assert checks["source_pack_downstream_boundary_visible"]["ok"] is True
    assert checks["source_pack_artifacts_added_create_only"]["ok"] is True
    assert checks["owned_process_terminated"]["ok"] is True


def test_packaged_capture_markdown_guard_failure_clickthrough_blocks_source_pack_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: fake_process.pid)
    monkeypatch.setattr(
        visual_qa,
        "_terminate_packaged_process_tree",
        lambda *_args, **_kwargs: {"attempted": True, "terminated": True, "returncode": 0},
    )
    monkeypatch.setattr(
        visual_qa,
        "_cleanup_new_pyinstaller_temp_dirs",
        lambda *_args, **_kwargs: {"attempted": True, "deleted": [], "failed": [], "reason": "test"},
    )
    monkeypatch.setattr(visual_qa, "_analyze_png_nonblank_and_content_area_dotnet", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(_args, *, env, **_kwargs):
        plan = json.loads(Path(env[visual_qa.QA_BATCH_PLAN_PATH_ENV]).read_text(encoding="utf-8"))
        route = plan["routes"][0]
        payload = route["capture_markdown_action"]
        assert route["id"] == visual_qa.CAPTURE_MARKDOWN_GUARD_FAILURE_PANEL_ID
        assert "guard_failure_mode" in route["action_script"]
        assert "capture-markdown-guard-failure" in route["action_script"]
        screenshot = Path(route["screenshot_path"])
        meta_path = Path(route["meta_path"])
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        pixels = [
            bytes(((x + y) % 256, (x * 2) % 256, (y * 3) % 256))
            for y in range(240)
            for x in range(320)
        ]
        _write_png(screenshot, 320, 240, pixels)
        meta_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "method": "qt_widget_grab",
                    "process_id": fake_process.pid,
                    "width": 320,
                    "height": 240,
                    "route_id": route["id"],
                    "route_hash": route["hash"],
                    "route_script": {
                        "start": {"ok": True, "result": {"ok": True, "started": True}},
                        "final": {
                            "ok": True,
                            "result": {
                                "ok": True,
                                "status": "guard_failure_visible",
                                "save_action_message": "Saved to quarantine.",
                                "action_message": "Review: reviewed.",
                                "preview_text": payload["preview_marker"],
                                "recent_text": f"{payload['title']} reviewed",
                                "source_card_proof": {
                                    "required_present": True,
                                    "approval_gated_downstream_visible": True,
                                    "explicit_browser_artifact_collector_visible": True,
                                    "explicit_browser_artifact_collector_settings_gated": True,
                                    "explicit_chaseos_browser_page_collector_visible": True,
                                    "explicit_chaseos_browser_page_collector_settings_gated": True,
                                    "explicit_discord_artifact_collector_visible": True,
                                    "explicit_discord_artifact_collector_settings_gated": True,
                                },
                                "release_readiness_proof": {
                                    "visible": True,
                                    "status": "partial_core_verified_optional_collectors_blocked",
                                    "approval_gated_downstream_visible": True,
                                },
                                "shortcut_proof": {
                                    "collector_shortcut_rows_visible": True,
                                    "collector_shortcut_rows_configurable": True,
                                },
                                "review_proof_before": {
                                    "title_visible": True,
                                    "review_controls_visible": True,
                                    "review_path_present": True,
                                    "item_text": payload["title"],
                                },
                                "review_proof_after": {
                                    "selected_decision": "reviewed",
                                    "item_text": f"{payload['title']} reviewed",
                                },
                                "source_pack_proof": {
                                    "preview_visible": True,
                                    "write_button_visible": True,
                                    "guard_failure_visible": True,
                                    "guard_failure_text": (
                                        "Source-pack write blocked blocked No downstream write "
                                        "operator_statement_mismatch"
                                    ),
                                    "text": "Source-Pack Approval Preview Source-pack write blocked No downstream write",
                                },
                                "body_text": (
                                    f"{payload['saved_message']} {payload['review_message']} "
                                    f"{payload['preview_marker']} {payload['title']} reviewed "
                                    "Source-pack write blocked No downstream write"
                                ),
                            },
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        result_path = Path(env[visual_qa.QA_BATCH_RESULT_PATH_ENV])
        result_path.write_text(
            json.dumps({"ok": True, "done": True, "captured_count": 1, "expected_count": 1, "results": []}),
            encoding="utf-8",
        )
        output_path = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources" / "guard-failure.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    f"# Capture to Markdown - {payload['title']}",
                    payload["raw_text"],
                    payload["source_url"],
                ]
            ),
            encoding="utf-8",
        )
        _write_capture_review_artifacts(output_path)
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)

    report = visual_qa.build_packaged_capture_markdown_guard_failure_clickthrough(
        tmp_path,
        executable_path=exe,
        screenshot_root=tmp_path / "evidence",
        settle_seconds=0.1,
        run_token="unit-token",
    )

    assert report["ok"] is True
    assert report["surface"] == "studio_packaged_capture_markdown_guard_failure_clickthrough"
    assert report["capture_mode"] == "manual_text_guard_failure"
    assert report["write_sentinel"]["source_pack_artifacts"] == {"added": [], "removed": [], "modified": []}
    assert report["write_sentinel"]["approval_artifacts"] == {"added": [], "removed": [], "modified": []}
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["source_pack_guard_failure_result_card_visible"]["ok"] is True
    assert checks["source_pack_guard_failure_writes_no_source_pack_artifacts"]["ok"] is True
    assert checks["source_pack_guard_failure_writes_no_approval_artifacts"]["ok"] is True
    assert checks["owned_process_terminated"]["ok"] is True


def test_packaged_capture_markdown_downstream_failure_clickthrough_blocks_after_source_pack_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: fake_process.pid)
    monkeypatch.setattr(
        visual_qa,
        "_terminate_packaged_process_tree",
        lambda *_args, **_kwargs: {"attempted": True, "terminated": True, "returncode": 0},
    )
    monkeypatch.setattr(
        visual_qa,
        "_cleanup_new_pyinstaller_temp_dirs",
        lambda *_args, **_kwargs: {"attempted": True, "deleted": [], "failed": [], "reason": "test"},
    )
    monkeypatch.setattr(visual_qa, "_analyze_png_nonblank_and_content_area_dotnet", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(_args, *, env, **_kwargs):
        plan = json.loads(Path(env[visual_qa.QA_BATCH_PLAN_PATH_ENV]).read_text(encoding="utf-8"))
        route = plan["routes"][0]
        payload = route["capture_markdown_action"]
        assert route["id"] == visual_qa.CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_PANEL_ID
        assert payload["downstream_failure_case_id"] == "aor_approval_request_bad_statement"
        assert "downstream_failure_mode" in route["action_script"]
        assert "failDownstreamStatement" in route["action_script"]
        screenshot = Path(route["screenshot_path"])
        meta_path = Path(route["meta_path"])
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        pixels = [
            bytes(((x + y) % 256, (x * 2) % 256, (y * 5) % 256))
            for y in range(240)
            for x in range(320)
        ]
        _write_png(screenshot, 320, 240, pixels)
        meta_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "method": "qt_widget_grab",
                    "process_id": fake_process.pid,
                    "width": 320,
                    "height": 240,
                    "route_id": route["id"],
                    "route_hash": route["hash"],
                    "route_script": {
                        "start": {"ok": True, "result": {"ok": True, "started": True}},
                        "final": {
                            "ok": True,
                            "result": {
                                "ok": True,
                                "status": "downstream_failure_visible",
                                "downstream_failure_case_id": payload["downstream_failure_case_id"],
                                "save_action_message": "Saved to quarantine.",
                                "action_message": "Review: reviewed.",
                                "preview_text": payload["preview_marker"],
                                "recent_text": f"{payload['title']} reviewed",
                                "source_card_proof": {
                                    "required_present": True,
                                },
                                "release_readiness_proof": {
                                    "visible": True,
                                    "status": "partial_core_verified_optional_collectors_blocked",
                                    "approval_gated_downstream_visible": True,
                                },
                                "shortcut_proof": {
                                    "collector_shortcut_rows_visible": True,
                                    "collector_shortcut_rows_configurable": True,
                                },
                                "review_proof_before": {
                                    "title_visible": True,
                                    "review_controls_visible": True,
                                    "review_path_present": True,
                                    "item_text": payload["title"],
                                },
                                "review_proof_after": {
                                    "selected_decision": "reviewed",
                                    "item_text": f"{payload['title']} reviewed",
                                },
                                "source_pack_proof": {
                                    "write_result_visible": True,
                                    "boundary_visible": True,
                                    "guard_failure_visible": True,
                                    "guard_failure_text": (
                                        "Agent Orchestration Runtime approval request blocked "
                                        "blocked No downstream write operator_statement_mismatch"
                                    ),
                                    "result_selectors": {
                                        ".capture-markdown-source-pack-aor-readiness": True,
                                        ".capture-markdown-source-pack-aor-approval-design": True,
                                        ".capture-markdown-source-pack-aor-approval-request": False,
                                    },
                                    "text": (
                                        "Source-Pack Write Agent Orchestration Runtime approval request blocked "
                                        "No downstream write"
                                    ),
                                },
                                "body_text": (
                                    f"{payload['saved_message']} {payload['review_message']} "
                                    f"{payload['preview_marker']} {payload['title']} reviewed "
                                    "Agent Orchestration Runtime approval request blocked No downstream write"
                                ),
                            },
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        result_path = Path(env[visual_qa.QA_BATCH_RESULT_PATH_ENV])
        result_path.write_text(
            json.dumps({"ok": True, "done": True, "captured_count": 1, "expected_count": 1, "results": []}),
            encoding="utf-8",
        )
        output_path = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources" / "downstream-failure.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    f"# Capture to Markdown - {payload['title']}",
                    payload["raw_text"],
                    payload["source_url"],
                ]
            ),
            encoding="utf-8",
        )
        _write_capture_review_artifacts(output_path)
        for name in ("manifest.json", "content.md", "provenance.json"):
            source_pack_path = tmp_path / "runtime" / "acquisition" / "packs" / "unit-downstream" / name
            source_pack_path.parent.mkdir(parents=True, exist_ok=True)
            source_pack_path.write_text("{}", encoding="utf-8")
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)

    report = visual_qa.build_packaged_capture_markdown_downstream_failure_clickthrough(
        tmp_path,
        case_id="aor_approval_request_bad_statement",
        executable_path=exe,
        screenshot_root=tmp_path / "evidence",
        settle_seconds=0.1,
        run_token="unit-token",
    )

    assert report["ok"] is True
    assert report["surface"] == "studio_packaged_capture_markdown_downstream_failure_clickthrough"
    assert report["capture_mode"] == "manual_text_downstream_failure:aor_approval_request_bad_statement"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["downstream_failure_guard_card_visible"]["ok"] is True
    assert checks["downstream_failure_reached_expected_boundary"]["ok"] is True
    assert checks["downstream_failure_forbidden_artifacts_not_written"]["ok"] is True
    assert checks["downstream_failure_source_pack_artifacts_added_create_only"]["ok"] is True
    assert checks["owned_process_terminated"]["ok"] is True


def test_packaged_capture_markdown_downstream_failure_state_matrix_runs_cases(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    def fake_clickthrough(vault_root, *, case_id, **kwargs):
        calls.append(case_id)
        return {
            "ok": True,
            "status": "packaged_capture_markdown_downstream_failure_clickthrough_complete",
            "screenshot": {"path": f"evidence/{case_id}.png"},
            "action_assessment": {
                "checks": [
                    {"name": "downstream_failure_guard_card_visible", "ok": True},
                    {"name": "downstream_failure_reached_expected_boundary", "ok": True},
                    {"name": "downstream_failure_forbidden_artifacts_not_written", "ok": True},
                ]
            },
            "blockers": [],
        }

    monkeypatch.setattr(
        visual_qa,
        "build_packaged_capture_markdown_downstream_failure_clickthrough",
        fake_clickthrough,
    )

    report = visual_qa.build_packaged_capture_markdown_downstream_failure_state_matrix(
        tmp_path,
        executable_path=tmp_path / "ChaseOS-Studio.exe",
        screenshot_root=tmp_path / "matrix-evidence",
        run_token="matrix-token",
    )

    assert report["ok"] is True
    assert report["case_count"] == len(visual_qa.CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_CASES)
    assert calls == [case["id"] for case in visual_qa.CAPTURE_MARKDOWN_DOWNSTREAM_FAILURE_CASES]
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["downstream_failure_guard_cards_visible"]["ok"] is True
    assert checks["downstream_failure_expected_boundaries_reached"]["ok"] is True
    assert checks["downstream_failure_forbidden_artifacts_not_written"]["ok"] is True


def test_packaged_capture_markdown_window_size_matrix_sets_proof_window_env(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_clickthrough(vault_root, **kwargs):
        env = dict(kwargs.get("env_overrides") or {})
        width = int(env[visual_qa.QA_WINDOW_WIDTH_ENV])
        height = int(env[visual_qa.QA_WINDOW_HEIGHT_ENV])
        calls.append(
            {
                "vault_root": vault_root,
                "screenshot_root": kwargs.get("screenshot_root"),
                "env_overrides": env,
                "run_token": kwargs.get("run_token"),
                "capture_mode": kwargs.get("capture_mode"),
            }
        )
        return {
            "ok": True,
            "status": "packaged_capture_markdown_guard_failure_clickthrough_complete",
            "screenshot": {
                "path": f"evidence/{width}x{height}.png",
                "size_bytes": width + height,
                "capture": {
                    "width": width * 2,
                    "height": height * 2,
                    "capture_method": "qt_widget_grab",
                },
            },
            "blockers": [],
        }

    monkeypatch.setattr(visual_qa, "build_packaged_capture_markdown_action_clickthrough", fake_clickthrough)

    report = visual_qa.build_packaged_capture_markdown_window_size_matrix(
        tmp_path,
        screenshot_root=tmp_path / "evidence",
        run_token="matrix-token",
        window_size_cases=["compact:1000x700", "wide:1600x1000"],
    )

    assert report["ok"] is True
    assert report["status"] == "packaged_capture_markdown_window_size_matrix_complete"
    assert [case["id"] for case in report["cases"]] == ["compact", "wide"]
    assert calls[0]["env_overrides"][visual_qa.QA_WINDOW_WIDTH_ENV] == "1000"
    assert calls[1]["env_overrides"][visual_qa.QA_WINDOW_HEIGHT_ENV] == "1000"
    assert calls[0]["run_token"] == "matrix-token-compact"
    assert calls[1]["run_token"] == "matrix-token-wide"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["window_size_requests_affect_capture_dimensions"]["ok"] is True
    assert report["authority"]["uses_proof_only_window_size_environment"] is True


def test_packaged_capture_markdown_image_text_clickthrough_accepts_expected_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: fake_process.pid)
    monkeypatch.setattr(
        visual_qa,
        "_terminate_packaged_process_tree",
        lambda *_args, **_kwargs: {"attempted": True, "terminated": True, "returncode": 0},
    )
    monkeypatch.setattr(
        visual_qa,
        "_cleanup_new_pyinstaller_temp_dirs",
        lambda *_args, **_kwargs: {"attempted": True, "deleted": [], "failed": [], "reason": "test"},
    )
    monkeypatch.setattr(visual_qa, "_analyze_png_nonblank_and_content_area_dotnet", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(_args, *, env, **_kwargs):
        plan = json.loads(Path(env[visual_qa.QA_BATCH_PLAN_PATH_ENV]).read_text(encoding="utf-8"))
        route = plan["routes"][0]
        payload = route["capture_markdown_action"]
        assert route["id"] == visual_qa.CAPTURE_MARKDOWN_IMAGE_TEXT_PANEL_ID
        assert route["script_wait_for_result"] is False
        assert "screenshot_text_extraction" in route["action_script"]
        assert payload["local_ocr_command"]
        screenshot = Path(route["screenshot_path"])
        meta_path = Path(route["meta_path"])
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        pixels = [
            bytes(((x + y) % 256, (x * 5) % 256, (y * 7) % 256))
            for y in range(240)
            for x in range(320)
        ]
        _write_png(screenshot, 320, 240, pixels)
        marker_path = tmp_path / payload["engine_marker_path"]
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("ran", encoding="utf-8")
        meta_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "method": "qt_widget_grab",
                    "process_id": fake_process.pid,
                    "width": 320,
                    "height": 240,
                    "route_id": route["id"],
                    "route_hash": route["hash"],
                    "route_script": {
                        "start": {"ok": True, "result": {"ok": True, "started": True}},
                        "final": {
                            "ok": True,
                            "result": {
                                "ok": True,
                                "status": "reviewed",
                                "save_action_message": "Saved to quarantine.",
                                "action_message": "Review: reviewed.",
                                "preview_text": payload["extracted_text"],
                                "recent_text": f"{payload['title']} reviewed",
                                "source_card_proof": {
                                    "optical_character_recognition_visible": True,
                                    "optical_character_recognition_selectable": True,
                                    "optical_character_recognition_local_status": "available_local_engine",
                                    "optical_character_recognition_selects_source_mode": True,
                                    "local_command_row_visible": True,
                                    "live_collectors_blocked": True,
                                    "explicit_screen_collector_settings_gated": True,
                                    "explicit_clipboard_collector_settings_gated": True,
                                    "downstream_consumers_visible": True,
                                },
                                "settings_proof": {
                                    "section_visible": True,
                                    "command_visible": True,
                                    "command_matches_saved_settings": True,
                                    "cloud_extraction_blocked": True,
                                    "screen_capture_blocked": True,
                                },
                                "form_payload_after_set": {
                                    "source_mode": "screenshot_text_extraction",
                                    "title": payload["title"],
                                    "file_path": payload["file_path"],
                                    "local_ocr_command": "",
                                },
                                "review_proof_before": {
                                    "title_visible": True,
                                    "review_controls_visible": True,
                                    "review_path_present": True,
                                    "item_text": payload["title"],
                                },
                                "review_proof_after": {
                                    "selected_decision": "reviewed",
                                    "item_text": f"{payload['title']} reviewed",
                                },
                                "body_text": (
                                    f"{payload['saved_message']} {payload['review_message']} "
                                    f"{payload['extracted_text']} {payload['title']} reviewed"
                                ),
                            },
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        result_path = Path(env[visual_qa.QA_BATCH_RESULT_PATH_ENV])
        result_path.write_text(
            json.dumps({"ok": True, "done": True, "captured_count": 1, "expected_count": 1, "results": []}),
            encoding="utf-8",
        )
        output_path = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "Sources" / f"{payload['token']}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    f"# Capture to Markdown - {payload['title']}",
                    payload["extracted_text"],
                    payload["source_url"],
                    "optical_character_recognition_status: text_extracted",
                ]
            ),
            encoding="utf-8",
        )
        _write_capture_review_artifacts(
            output_path,
            capture_method="screenshot_local_text_extraction",
            extraction_status="text_extracted",
            local_image_text=True,
        )
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)

    report = visual_qa.build_packaged_capture_markdown_image_text_clickthrough(
        tmp_path,
        executable_path=exe,
        screenshot_root=tmp_path / "evidence",
        settle_seconds=0.1,
        run_token="image-token",
    )

    assert report["ok"] is True
    assert report["surface"] == "studio_packaged_capture_markdown_image_text_clickthrough"
    assert report["temporary_settings"]["restored"] is True
    assert not (tmp_path / "runtime" / "studio" / "state" / "capture-local-image-text.json").exists()
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["settings_capture_image_text_section_visible"]["ok"] is True
    assert checks["capture_optical_character_recognition_selects_image_text_mode"]["ok"] is True
    assert checks["per_capture_command_blank_so_settings_command_is_used"]["ok"] is True
    assert checks["output_markdown_contains_extracted_image_text"]["ok"] is True
    assert checks["review_sidecar_records_image_text_extraction"]["ok"] is True
    assert checks["owned_process_terminated"]["ok"] is True


def test_packaged_capture_markdown_image_text_failure_clickthrough_blocks_expected_failures(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: fake_process.pid)
    monkeypatch.setattr(
        visual_qa,
        "_terminate_packaged_process_tree",
        lambda *_args, **_kwargs: {"attempted": True, "terminated": True, "returncode": 0},
    )
    monkeypatch.setattr(
        visual_qa,
        "_cleanup_new_pyinstaller_temp_dirs",
        lambda *_args, **_kwargs: {"attempted": True, "deleted": [], "failed": [], "reason": "test"},
    )
    monkeypatch.setattr(visual_qa, "_analyze_png_nonblank_and_content_area_dotnet", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(_args, *, env, **_kwargs):
        plan = json.loads(Path(env[visual_qa.QA_BATCH_PLAN_PATH_ENV]).read_text(encoding="utf-8"))
        route = plan["routes"][0]
        payload = route["capture_markdown_action"]
        assert route["id"] == visual_qa.CAPTURE_MARKDOWN_IMAGE_TEXT_FAILURE_PANEL_ID
        assert route["script_wait_for_result"] is False
        assert "failure_states_visible" in route["action_script"]
        assert "screenshot_text_extraction" in route["action_script"]
        assert payload["failure_cases"]
        screenshot = Path(route["screenshot_path"])
        meta_path = Path(route["meta_path"])
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        pixels = [
            bytes(((x + y) % 256, (x * 3) % 256, (y * 11) % 256))
            for y in range(240)
            for x in range(320)
        ]
        _write_png(screenshot, 320, 240, pixels)
        failure_cases = []
        for item in payload["failure_cases"]:
            marker_path = item.get("marker_path") or ""
            if marker_path:
                marker = tmp_path / marker_path
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text("ran", encoding="utf-8")
            failure_cases.append(
                {
                    "id": item["id"],
                    "ok": True,
                    "expected_text": item["expected_text"],
                    "expected_status": item["expected_status"],
                    "preview_text": item["expected_text"],
                    "action_message": item["expected_text"],
                    "save_disabled": True,
                    "form_payload_after_set": {
                        "source_mode": "screenshot_text_extraction",
                        "title": item["title"],
                        "file_path": payload["file_path"],
                        "local_ocr_command": item["local_ocr_command"],
                    },
                    "body_text": f"{item['expected_text']} {item['title']}",
                }
            )
        meta_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "method": "qt_widget_grab",
                    "process_id": fake_process.pid,
                    "width": 320,
                    "height": 240,
                    "route_id": route["id"],
                    "route_hash": route["hash"],
                    "route_script": {
                        "start": {"ok": True, "result": {"ok": True, "started": True}},
                        "final": {
                            "ok": True,
                            "result": {
                                "ok": True,
                                "status": "failure_states_visible",
                                "source_card_proof": {
                                    "optical_character_recognition_visible": True,
                                    "optical_character_recognition_selectable": True,
                                    "optical_character_recognition_local_status": "available_local_engine_required",
                                    "optical_character_recognition_selects_source_mode": True,
                                    "local_command_row_visible": True,
                                    "live_collectors_blocked": True,
                                    "explicit_screen_collector_settings_gated": True,
                                    "explicit_clipboard_collector_settings_gated": True,
                                    "downstream_consumers_visible": True,
                                },
                                "settings_proof": {
                                    "section_visible": True,
                                    "command_visible": True,
                                    "command_blank": True,
                                    "timeout_visible": True,
                                    "timeout_matches_saved_settings": True,
                                    "cloud_extraction_blocked": True,
                                    "screen_capture_blocked": True,
                                },
                                "failure_cases": failure_cases,
                                "body_text": " ".join(item["expected_text"] for item in payload["failure_cases"]),
                            },
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        result_path = Path(env[visual_qa.QA_BATCH_RESULT_PATH_ENV])
        result_path.write_text(
            json.dumps({"ok": True, "done": True, "captured_count": 1, "expected_count": 1, "results": []}),
            encoding="utf-8",
        )
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)

    report = visual_qa.build_packaged_capture_markdown_image_text_failure_clickthrough(
        tmp_path,
        executable_path=exe,
        screenshot_root=tmp_path / "evidence",
        settle_seconds=0.1,
        run_token="failure-token",
    )

    assert report["ok"] is True
    assert report["surface"] == "studio_packaged_capture_markdown_image_text_failure_states"
    assert report["capture_mode"] == "image_text_failure"
    assert report["authority"]["writes_raw_quarantine_markdown"] is False
    assert report["temporary_settings"]["restored"] is True
    assert not (tmp_path / "runtime" / "studio" / "state" / "capture-local-image-text.json").exists()
    assert report["write_sentinel"]["markdown"]["added"] == []
    assert all("local_ocr_command" not in item for item in report["payload"]["failure_cases"])
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["settings_capture_image_text_failure_section_visible"]["ok"] is True
    assert checks["capture_failure_optical_character_recognition_selects_image_text_mode"]["ok"] is True
    assert checks["all_expected_image_text_failure_cases_recorded"]["ok"] is True
    assert checks["image_text_failure_case_missing_engine_visible"]["ok"] is True
    assert checks["image_text_failure_case_timeout_save_disabled"]["ok"] is True
    assert checks["image_text_failure_case_sensitive_extracted_text_visible"]["ok"] is True
    assert checks["image_text_failure_states_write_no_raw_quarantine_markdown"]["ok"] is True
    assert checks["image_text_failure_states_write_no_approval_artifacts"]["ok"] is True
    assert checks["owned_process_terminated"]["ok"] is True


def test_packaged_visual_qa_uses_resolved_windows_pid_for_native_capture(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    captured = {}

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)
    monkeypatch.setattr(
        visual_qa,
        "_resolve_windows_process_id_for_packaged_exe",
        lambda **_kwargs: 34567,
    )

    def fake_capture(**kwargs):
        captured.update(kwargs)
        return {"ok": False, "error": "window_handle_not_found"}

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        settle_seconds=0.1,
    )

    assert captured["process_id"] == 34567
    assert report["launch"]["process_id"] == fake_process.pid
    assert report["launch"]["windows_process_id"] == 34567
    assert fake_process.terminated is True


def test_packaged_visual_qa_passes_initial_hash_to_native_app(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: 34567)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {"ok": False, "error": "window_handle_not_found"},
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        initial_hash="chat",
        settle_seconds=0.1,
    )

    assert "--initial-hash" in captured["args"]
    assert "#/chat" in captured["args"]
    assert report["launch"]["initial_hash"] == "#/chat"


def test_packaged_visual_qa_caps_internal_screenshot_delay_after_loaded_event(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    popen_kwargs: dict[str, object] = {}

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(_args, **kwargs):
        popen_kwargs.update(kwargs)
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: 34567)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {"ok": False, "error": "window_handle_not_found"},
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        settle_seconds=8,
    )

    assert popen_kwargs["env"][visual_qa.QA_SCREENSHOT_DELAY_MS_ENV] == "1500"
    assert report["launch"]["qa_screenshot_delay_ms"] == 1500


def test_packaged_visual_qa_prefers_external_window_capture_over_internal_qt_capture(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "visual.png"
    fake_process = FakeProcess(alive=True)
    reads = {"count": 0}

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_internal_capture(_meta_path, screenshot_path):
        reads["count"] += 1
        if reads["count"] == 1:
            return {"ok": False, "error": "internal_qa_capture_meta_missing"}
        width = 320
        height = 220
        colors = [b"\x0f\x17\x2a", b"\x38\xbd\xf8", b"\xf8\xfa\xfc", b"\x22\xc5\x5e"]
        pixels = [colors[(x + y) % len(colors)] for y in range(height) for x in range(width)]
        path = Path(screenshot_path)
        _write_png(path, width, height, pixels)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "path": str(path),
            "width": 900,
            "height": 700,
            "window_title": "ChaseOS Studio - test",
            "ui_automation_text": "ChaseOS Studio home chat workspaces graph agents / runtimes",
            "capture_method": "qt_widget_grab",
            "size_bytes": path.stat().st_size,
        }

    def fake_external_capture(**kwargs):
        width = 320
        height = 220
        colors = [b"\x12\x22\x3a", b"\x2dd4bf", b"\xf8\xfa\xfc", b"\x60\xa5\xfa"]
        path = Path(kwargs["screenshot_path"])
        pixels = [colors[(x + y) % len(colors)] for y in range(height) for x in range(width)]
        _write_png(path, width, height, pixels)
        path.write_bytes(path.read_bytes() + (b"y" * 2048))
        return {
            "ok": True,
            "path": str(path),
            "width": 900,
            "height": 700,
            "window_title": "ChaseOS Studio - test",
            "ui_automation_text": "ChaseOS Studio home chat workspaces graph agents / runtimes",
            "capture_method": "copy_from_screen",
            "size_bytes": path.stat().st_size,
        }

    monkeypatch.setattr(visual_qa, "_read_internal_qa_capture", fake_internal_capture)
    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_external_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    assert reads["count"] >= 2
    assert report["screenshot"]["exists"] is True
    assert report["screenshot"]["capture"]["capture_method"] == "copy_from_screen"
    assert fake_process.terminated is True


def test_packaged_visual_qa_uses_workspace_temp_root_and_cleans_new_mei_dirs(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "visual.png"
    fake_process = FakeProcess(alive=True)
    popen_kwargs: dict[str, object] = {}

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(_args, **kwargs):
        popen_kwargs.update(kwargs)
        return fake_process

    def fake_capture(**_kwargs):
        temp_root = Path(dict(popen_kwargs["env"])["TEMP"])
        leaked_mei = temp_root / "_MEI123456"
        leaked_mei.mkdir(parents=True)
        (leaked_mei / "payload.bin").write_bytes(b"x" * 1024)
        width = 320
        height = 220
        colors = [b"\x0f\x17\x2a", b"\x38\xbd\xf8", b"\xf8\xfa\xfc", b"\x22\xc5\x5e"]
        pixels = [colors[(x + y) % len(colors)] for y in range(height) for x in range(width)]
        _write_png(screenshot, width, height, pixels)
        return {
            "ok": True,
            "path": str(screenshot),
            "width": 900,
            "height": 700,
            "window_title": "ChaseOS Studio - test",
            "ui_automation_text": "ChaseOS Studio home chat workspaces graph agents / runtimes",
            "capture_method": "copy_from_screen",
            "size_bytes": screenshot.stat().st_size,
        }

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(visual_qa, "_resolve_windows_process_id_for_packaged_exe", lambda **_kwargs: 34567)
    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    temp_root = Path(dict(popen_kwargs["env"])["TEMP"])
    assert temp_root == (tmp_path / visual_qa.DEFAULT_PACKAGED_QA_TEMP_ROOT).resolve()
    assert report["launch"]["runtime_dirs"]["uses_default_temp_root"] is True
    cleanup = report["termination"]["pyinstaller_temp_cleanup"]
    assert cleanup["deleted_count"] == 1
    assert not (temp_root / "_MEI123456").exists()
    assert report["screenshot"]["capture"]["ok"] is True


def test_packaged_visual_qa_defers_large_pyinstaller_temp_cleanup(tmp_path: Path) -> None:
    temp_root = tmp_path / "temp"
    leaked_mei = temp_root / "_MEI999999"
    leaked_mei.mkdir(parents=True)
    for index in range(visual_qa.MAX_PYINSTALLER_TEMP_CLEANUP_ENTRIES + 1):
        (leaked_mei / f"payload-{index}.bin").write_bytes(b"x")

    before = {"root": str(temp_root), "paths": []}
    env = {"TEMP": str(temp_root), "TMP": str(temp_root), "TMPDIR": str(temp_root)}
    cleanup = visual_qa._cleanup_new_pyinstaller_temp_dirs(before, env)

    assert cleanup["deleted_count"] == 0
    assert cleanup["failed"]
    assert "cleanup deferred" in cleanup["failed"][0]["error"]
    assert leaked_mei.exists()


def test_packaged_all_pages_page_report_uses_combined_png_analysis(tmp_path: Path) -> None:
    screenshot = tmp_path / "combined-analysis.png"
    width = 320
    height = 260
    colors = [b"\x0f\x17\x2a", b"\x38\xbd\xf8", b"\xf8\xfa\xfc", b"\x22\xc5\x5e"]
    pixels = [colors[(x + y) % len(colors)] for y in range(height) for x in range(width)]
    _write_png(screenshot, width, height, pixels)

    visual, content = visual_qa._analyze_png_nonblank_and_content_area(
        screenshot,
        min_unique_colors=2,
        max_dominant_ratio=0.95,
    )

    assert visual["ok"] is True
    assert content["ok"] is True
    assert visual["reason"] == "nonblank"
    assert content["reason"] == "content-area-nonblank"


def test_packaged_all_pages_visual_qa_aggregates_route_reports(monkeypatch, tmp_path: Path) -> None:
    from runtime.studio import final_productization_visual_qa

    panels = (
        {"id": "dashboard", "name": "Home", "hash": "#/dashboard"},
        {"id": "chat", "name": "Chat", "hash": "#/chat"},
    )
    captured: list[dict[str, object]] = []

    monkeypatch.setattr(final_productization_visual_qa, "PANELS", panels)

    def fake_build(vault_root, **kwargs):
        captured.append(kwargs)
        screenshot = Path(kwargs["screenshot_path"])
        color = b"\x38\xbd\xf8" if len(captured) == 1 else b"\x22\xc5\x5e"
        _write_png(screenshot, 12, 12, [color] * 144)
        screenshot.write_bytes(screenshot.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "status": "packaged_app_visual_qa_complete",
            "screenshot": {"path": str(screenshot.relative_to(tmp_path)), "exists": True},
            "launch": {"initial_hash": kwargs.get("initial_hash")},
            "termination": {"terminated": True},
            "checks": [],
            "blockers": [],
        }

    monkeypatch.setattr(visual_qa, "build_packaged_app_visual_qa", fake_build)

    report = visual_qa.build_packaged_app_all_pages_visual_qa(
        tmp_path,
        screenshot_root="screens",
        webview2_user_data_root="runtime-dirs/webview2",
        temp_root="runtime-dirs/temp",
        settle_seconds=0.1,
        batch_launch=False,
    )

    assert report["ok"] is True
    assert report["page_count"] == 2
    assert report["failed_page_count"] == 0
    assert [item["initial_hash"] for item in captured] == ["#/dashboard", "#/chat"]
    assert [item["webview2_user_data_root"] for item in captured] == [
        Path("runtime-dirs/webview2/dashboard"),
        Path("runtime-dirs/webview2/chat"),
    ]
    assert [item["temp_root"] for item in captured] == [
        Path("runtime-dirs/temp/dashboard"),
        Path("runtime-dirs/temp/chat"),
    ]
    assert (tmp_path / "screens").is_dir()


def test_packaged_all_pages_visual_qa_retries_markdown_sentinel_only_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from runtime.studio import final_productization_visual_qa

    panels = ({"id": "dashboard", "name": "Home", "hash": "#/dashboard"},)
    calls: list[Path] = []
    temp_roots: list[Path] = []

    monkeypatch.setattr(final_productization_visual_qa, "PANELS", panels)

    def fake_build(vault_root, **kwargs):
        screenshot = Path(kwargs["screenshot_path"])
        calls.append(screenshot)
        temp_roots.append(Path(kwargs["temp_root"]))
        color = b"\x38\xbd\xf8" if len(calls) == 1 else b"\x22\xc5\x5e"
        _write_png(screenshot, 12, 12, [color] * 144)
        screenshot.write_bytes(screenshot.read_bytes() + (b"x" * 2048))
        if len(calls) == 1:
            return {
                "ok": False,
                "status": "blocked_packaged_app_visual_qa",
                "screenshot": {"path": screenshot.name, "exists": True},
                "launch": {"initial_hash": kwargs.get("initial_hash")},
                "termination": {"terminated": True},
                "write_sentinel": {
                    "markdown": {
                        "added": [],
                        "removed": [],
                        "modified": ["06_AGENTS/Codex-Runtime-Profile.md"],
                    },
                    "approval_artifacts": {"added": [], "removed": [], "modified": []},
                },
                "checks": [
                    {"name": "window_capture_ok", "ok": True, "detail": "window screenshot captured"},
                    {"name": "screenshot_exists", "ok": True, "detail": screenshot.name},
                    {"name": "screenshot_nonempty", "ok": True, "detail": "2048"},
                    {"name": "screenshot_nonblank", "ok": True, "detail": "nonblank"},
                    {"name": "screenshot_content_area_nonblank", "ok": True, "detail": "nonblank"},
                    {"name": "screenshot_studio_content_sentinel", "ok": True, "detail": "studio-content-sentinel-present"},
                    {"name": "screenshot_no_dev_visible_copy", "ok": True, "detail": "no-forbidden-copy"},
                    {"name": "window_bounds_valid", "ok": True, "detail": "900 x 700"},
                    {"name": "owned_process_terminated", "ok": True, "detail": "terminated only the process started by visual QA"},
                    {
                        "name": "no_markdown_writes",
                        "ok": False,
                        "detail": "modified: 06_AGENTS/Codex-Runtime-Profile.md",
                    },
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "snapshot unchanged"},
                ],
                "blockers": ["Markdown write sentinel changed during packaged visual QA."],
                "next_recommended_pass": "studio-packaged-app-visual-qa",
            }
        return {
            "ok": True,
            "status": "packaged_app_visual_qa_complete",
            "screenshot": {"path": screenshot.name, "exists": True},
            "launch": {"initial_hash": kwargs.get("initial_hash")},
            "termination": {"terminated": True},
            "checks": [{"name": "no_markdown_writes", "ok": True, "detail": "snapshot unchanged"}],
            "blockers": [],
            "next_recommended_pass": "studio-installer-plan-and-governance",
        }

    monkeypatch.setattr(visual_qa, "build_packaged_app_visual_qa", fake_build)

    report = visual_qa.build_packaged_app_all_pages_visual_qa(
        tmp_path,
        screenshot_root="screens",
        settle_seconds=0.1,
        batch_launch=False,
    )

    assert report["ok"] is True
    assert report["failed_page_count"] == 0
    assert report["markdown_sentinel_retried_page_count"] == 1
    assert calls == [tmp_path / "screens" / "dashboard.png", tmp_path / "screens" / "dashboard-retry1.png"]
    assert temp_roots == [
        visual_qa.DEFAULT_PACKAGED_QA_TEMP_ROOT / "dashboard",
        visual_qa.DEFAULT_PACKAGED_QA_TEMP_ROOT / "dashboard-retry1",
    ]
    assert report["pages"][0]["retry"]["final_ok"] is True


def test_packaged_all_pages_visual_qa_blocks_identical_route_screenshots(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from runtime.studio import final_productization_visual_qa

    panels = (
        {"id": "dashboard", "name": "Home", "hash": "#/dashboard"},
        {"id": "chat", "name": "Chat", "hash": "#/chat"},
        {"id": "graph", "name": "Graph", "hash": "#/graph"},
        {"id": "aor", "name": "Tasks & Runs", "hash": "#/aor"},
    )

    monkeypatch.setattr(final_productization_visual_qa, "PANELS", panels)

    def fake_build(vault_root, **kwargs):
        screenshot = Path(kwargs["screenshot_path"])
        _write_png(screenshot, 12, 12, [b"\x38\xbd\xf8"] * 144)
        screenshot.write_bytes(screenshot.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "status": "packaged_app_visual_qa_complete",
            "screenshot": {"path": str(screenshot.relative_to(tmp_path)), "exists": True},
            "launch": {"initial_hash": kwargs.get("initial_hash")},
            "termination": {"terminated": True},
            "checks": [],
            "blockers": [],
            "next_recommended_pass": "studio-installer-plan-and-governance",
        }

    monkeypatch.setattr(visual_qa, "build_packaged_app_visual_qa", fake_build)

    report = visual_qa.build_packaged_app_all_pages_visual_qa(
        tmp_path,
        screenshot_root="screens",
        settle_seconds=0.1,
        batch_launch=False,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert "route_screenshot_uniqueness_missing" in report["blockers"]
    assert checks["route_screenshots_unique"]["ok"] is False
    assert report["screenshot_hashes"]["unique_hash_count"] == 1


def test_screenshot_hash_summary_rejects_any_duplicate_route_image(tmp_path: Path) -> None:
    colors = [b"\x11\x22\x33", b"\x44\x55\x66", b"\x77\x88\x99"]
    reports = []
    for idx, color in enumerate(colors):
        path = tmp_path / f"route-{idx}.png"
        _write_png(path, 4, 4, [color] * 16)
        reports.append({"panel_id": f"route-{idx}", "screenshot": {"path": str(path)}})
    duplicate = tmp_path / "route-duplicate.png"
    _write_png(duplicate, 4, 4, [colors[0]] * 16)
    reports.append({"panel_id": "route-duplicate", "screenshot": {"path": str(duplicate)}})

    summary = visual_qa._screenshot_hash_summary(tmp_path, reports)

    assert summary["ok"] is False
    assert summary["unique_hash_count"] == 3
    assert summary["minimum_unique_hashes"] == 2
    assert summary["duplicate_group_count"] == 1
    assert summary["reason"] == "route-screenshot-uniqueness-missing"




def test_capture_window_screenshot_returns_structured_print_window_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    class FakeCompletedProcess:
        returncode = 4
        stdout = json.dumps(
            {
                "ok": False,
                "error": "print_window_failed",
                "process_id": 123,
                "window_process_id": 456,
                "window_title": "ChaseOS Studio",
                "ui_automation_text": "ChaseOS Studio Dashboard",
                "handle": 789,
                "left": 10,
                "top": 20,
                "width": 900,
                "height": 700,
                "print_window_exception": "PrintWindow returned false",
            }
        )
        stderr = ""

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["script"] = args[-1]
        captured["kwargs"] = kwargs
        return FakeCompletedProcess()

    monkeypatch.setattr(visual_qa.subprocess, "run", fake_run)

    report = visual_qa._capture_window_screenshot(
        process_id=123,
        screenshot_path=tmp_path / "native.png",
        timeout_seconds=0.1,
    )

    assert "print_window_failed" in str(captured["script"])
    assert "PrintWindow" in str(captured["script"])
    assert report["ok"] is False
    assert report["error"] == "print_window_failed"
    assert report["print_window_exception"] == "PrintWindow returned false"
    assert report["ui_automation_text"] == "ChaseOS Studio Dashboard"
    assert report["handle"] == 789
    assert report["returncode"] == 4


def test_packaged_visual_qa_classifies_windows_application_control_block(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )

    def fake_popen(*_args, **_kwargs):
        raise OSError("[WinError 4551] An Application Control policy has blocked this file")

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert report["status"] == "blocked_packaged_app_visual_qa"
    assert report["host_policy"]["status"] == "blocked_by_windows_application_control"
    assert report["host_policy"]["blocked_by_windows_application_control"] is True
    assert checks["host_policy_allows_launch"]["ok"] is False
    assert checks["host_policy_allows_launch"]["detail"] == "blocked_by_windows_application_control"
    assert report["screenshot"]["visual_verification"]["reason"] == "file-missing"
    assert report["next_recommended_pass"] == "pass10b-native-host-policy-unblock"


def test_packaged_visual_qa_classifies_webview2_initialization_failure(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(
        alive=True,
        stderr="[pywebview] WebView2 initialization failed with exception: E_UNEXPECTED",
    )

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {"ok": False, "error": "invalid_window_bounds", "width": 0, "height": 0},
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert report["launch"]["runtime_error"]["status"] == "webview2_initialization_failed"
    assert any("PyWebView/WebView2 initialization failed" in blocker for blocker in report["blockers"])
    assert checks["webview2_runtime_initialized"]["ok"] is False
    assert report["next_recommended_pass"] == "pass10b-webview2-runtime-diagnostic"


def test_packaged_visual_qa_classifies_pywebview_backend_startup_log(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    screenshot = tmp_path / "visual.png"
    screenshot.with_suffix(".startup.log").write_text(
        "webview.errors.WebViewException: You must have pythonnet installed in order to use pywebview.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {"ok": False, "error": "window_handle_not_found"},
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert report["launch"]["runtime_error"]["status"] == "pywebview_backend_dependency_missing"
    assert "PyWebView backend dependency is missing before native screenshot capture." in report["blockers"]
    assert checks["webview2_runtime_initialized"]["ok"] is False
    assert report["next_recommended_pass"] == "pass10b-pywebview-runtime-diagnostic"


def test_packaged_visual_qa_passes_environment_overrides(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    popen_kwargs = {}

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(*_args, **kwargs):
        popen_kwargs.update(kwargs)
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {"ok": False, "error": "window_handle_not_found"},
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        env_overrides={"WEBVIEW2_USER_DATA_FOLDER": str(tmp_path / "userdata")},
        settle_seconds=0.1,
    )

    assert popen_kwargs["env"]["WEBVIEW2_USER_DATA_FOLDER"] == str(tmp_path / "userdata")
    assert report["launch"]["env_override_keys"] == ["WEBVIEW2_USER_DATA_FOLDER"]


def test_packaged_visual_qa_runtime_dirs_set_webview2_and_temp_env(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    fake_process = FakeProcess(alive=True)
    popen_kwargs = {}

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)

    def fake_popen(*_args, **kwargs):
        popen_kwargs.update(kwargs)
        return fake_process

    monkeypatch.setattr(visual_qa.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        visual_qa,
        "_capture_window_screenshot",
        lambda **_kwargs: {"ok": False, "error": "window_handle_not_found"},
    )

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=tmp_path / "visual.png",
        webview2_user_data_root="runtime-dirs/webview2",
        temp_root="runtime-dirs/temp",
        settle_seconds=0.1,
    )

    expected_user_data = str((tmp_path / "runtime-dirs" / "webview2").resolve())
    expected_temp = str((tmp_path / "runtime-dirs" / "temp").resolve())
    assert popen_kwargs["env"]["WEBVIEW2_USER_DATA_FOLDER"] == expected_user_data
    assert popen_kwargs["env"]["TEMP"] == expected_temp
    assert popen_kwargs["env"]["TMP"] == expected_temp
    assert popen_kwargs["env"]["TMPDIR"] == expected_temp
    assert report["launch"]["runtime_env_override_keys"] == [
        "TEMP",
        "TMP",
        "TMPDIR",
        "WEBVIEW2_USER_DATA_FOLDER",
    ]
    assert report["launch"]["runtime_dirs"]["webview2_user_data_root"] == expected_user_data
    assert report["launch"]["runtime_dirs"]["temp_root"] == expected_temp


def test_packaged_visual_qa_rejects_external_runtime_dirs_by_default(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside-temp"

    with pytest.raises(ValueError, match="must stay inside the vault workspace"):
        visual_qa.build_runtime_env_overrides(vault, temp_root=outside)


def test_packaged_visual_qa_allows_external_runtime_dirs_when_explicit(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside_user_data = tmp_path / "outside-user-data"
    outside_temp = tmp_path / "outside-temp"

    overrides, runtime_dirs = visual_qa.build_runtime_env_overrides(
        vault,
        webview2_user_data_root=outside_user_data,
        temp_root=outside_temp,
        allow_external_runtime_dirs=True,
    )

    assert overrides["WEBVIEW2_USER_DATA_FOLDER"] == str(outside_user_data.resolve())
    assert overrides["TEMP"] == str(outside_temp.resolve())
    assert overrides["TMP"] == str(outside_temp.resolve())
    assert overrides["TMPDIR"] == str(outside_temp.resolve())
    assert runtime_dirs["allow_external_runtime_dirs"] is True
    assert outside_user_data.is_dir()
    assert outside_temp.is_dir()


def test_packaged_visual_qa_captures_screenshot_and_terminates(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "visual.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        colors = [
            b"\xff\xff\xff",
            b"\x00\x00\x00",
            b"\x38\xbd\xf8",
            b"\x63\x66\xf1",
            b"\x22\xc5\x5e",
            b"\xef\x44\x44",
            b"\xfa\xcc\x15",
            b"\xa8\x55\xf7",
        ]
        pixels = colors * 350
        path = Path(kwargs["screenshot_path"])
        _write_png(path, 70, 40, pixels)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": path.stat().st_size,
            "capture_method": "print_window",
            "ui_automation_text": "ChaseOS Studio Product Shell Home Command Center Chat Workspaces Graph",
        }

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    assert report["ok"] is True
    assert report["status"] == "packaged_app_visual_qa_complete"
    assert report["screenshot"]["exists"] is True
    assert report["authority"]["captures_native_screenshot"] is True
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["window_bounds_valid"]["ok"] is True
    assert checks["host_policy_allows_launch"]["ok"] is True
    assert checks["screenshot_nonblank"]["ok"] is True
    assert checks["screenshot_content_area_nonblank"]["ok"] is True
    assert checks["screenshot_studio_content_sentinel"]["ok"] is True
    assert checks["screenshot_no_dev_visible_copy"]["ok"] is True
    assert report["screenshot"]["visual_verification"]["ok"] is True
    assert report["screenshot"]["studio_content_sentinel"]["ok"] is True
    assert report["screenshot"]["forbidden_visible_copy"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True
    assert fake_process.terminated is True


def test_packaged_visual_qa_accepts_packaged_window_title_as_studio_content_sentinel(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "visual-title-sentinel.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        colors = [
            b"\xff\xff\xff",
            b"\x00\x00\x00",
            b"\x38\xbd\xf8",
            b"\x63\x66\xf1",
            b"\x22\xc5\x5e",
            b"\xef\x44\x44",
            b"\xfa\xcc\x15",
            b"\xa8\x55\xf7",
        ]
        path = Path(kwargs["screenshot_path"])
        _write_png(path, 70, 40, colors * 350)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": path.stat().st_size,
            "capture_method": "print_window",
            "window_title": "ChaseOS Studio Product Shell - chaseos_obsidian",
        }

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is True
    assert checks["screenshot_studio_content_sentinel"]["ok"] is True
    assert report["screenshot"]["studio_content_sentinel"]["sources_checked"] == ["window_title"]
    assert fake_process.terminated is True


def test_packaged_visual_qa_blocks_startup_loading_overlay_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "visual-loading.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        colors = [
            b"\xff\xff\xff",
            b"\x00\x00\x00",
            b"\x38\xbd\xf8",
            b"\x63\x66\xf1",
            b"\x22\xc5\x5e",
            b"\xef\x44\x44",
            b"\xfa\xcc\x15",
            b"\xa8\x55\xf7",
        ]
        path = Path(kwargs["screenshot_path"])
        _write_png(path, 70, 40, colors * 350)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": path.stat().st_size,
            "capture_method": "copy_from_screen",
            "window_title": "ChaseOS Studio Shell - chaseos_obsidian - Workspaces",
            "ui_automation_text": (
                "ChaseOS Studio | Starting ChaseOS Studio... | Opening workspace | Loading... | Open Workspaces | WORKSPACE | Loading vault..."
            ),
        }

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert checks["screenshot_studio_content_sentinel"]["ok"] is True
    assert checks["screenshot_no_startup_loading_visible"]["ok"] is False
    assert report["screenshot"]["startup_loading_visible_copy"]["matches"] == [
        "starting chaseos studio",
        "opening workspace",
        "loading...",
        "loading vault",
    ]
    assert (
        "Native UI is still showing startup/loading copy: starting chaseos studio, opening workspace, loading..., loading vault."
        in report["blockers"]
    )
    assert report["next_recommended_pass"] == "pass10b-native-window-content-sentinel-diagnostic"
    assert fake_process.terminated is True


def test_packaged_visual_qa_blocks_blank_webview_even_with_route_title(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "blank-webview.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        width = 100
        height = 140
        accent_colors = [
            b"\xee\xee\xee",
            b"\xdd\xdd\xdd",
            b"\xcc\xcc\xcc",
            b"\xbb\xbb\xbb",
        ]
        pixels: list[bytes] = []
        for y in range(height):
            for x in range(width):
                if y < visual_qa.CONTENT_AREA_TOP_SKIP_PIXELS:
                    pixels.append(accent_colors[(x + y) % len(accent_colors)])
                elif (x + y) % 40 == 0:
                    pixels.append(accent_colors[(x + y) % len(accent_colors)])
                else:
                    pixels.append(b"\xff\xff\xff")
        path = Path(kwargs["screenshot_path"])
        _write_png(path, width, height, pixels)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": path.stat().st_size,
            "capture_method": "copy_from_screen",
            "window_title": "ChaseOS Studio Shell - chaseos_obsidian - Workspaces",
            "ui_automation_text": "ChaseOS Studio Shell - chaseos_obsidian - Workspaces",
        }

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        initial_hash="#/project-workspace",
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    content_area = report["screenshot"]["content_area_verification"]
    assert report["ok"] is False
    assert checks["screenshot_studio_content_sentinel"]["ok"] is True
    assert checks["screenshot_content_area_nonblank"]["ok"] is False
    assert content_area["dominant_color_ratio"] > visual_qa.DEFAULT_MAX_DOMINANT_RATIO
    assert "Native window screenshot content area is blank or near-uniform." in report["blockers"]
    assert report["next_recommended_pass"] == "pass10b-native-window-content-sentinel-diagnostic"
    assert fake_process.terminated is True


def test_packaged_all_pages_visual_qa_accepts_route_title_when_uia_text_is_empty(
    tmp_path: Path,
) -> None:
    screenshot = tmp_path / "review-queue.png"
    colors = [
        b"\xff\xff\xff",
        b"\x00\x00\x00",
        b"\x38\xbd\xf8",
        b"\x63\x66\xf1",
        b"\x22\xc5\x5e",
        b"\xef\x44\x44",
        b"\xfa\xcc\x15",
        b"\xa8\x55\xf7",
    ]
    _write_png(screenshot, 70, 40, colors * 350)
    screenshot.write_bytes(screenshot.read_bytes() + (b"x" * 2048))

    report = visual_qa._build_all_pages_page_report(
        vault=tmp_path,
        panel={"id": "pulse-enqueue", "name": "Review Queue", "hash": "#/pulse-enqueue"},
        screenshot=screenshot,
        capture={
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": screenshot.stat().st_size,
            "capture_method": "copy_from_screen",
            "window_title": "ChaseOS Studio Shell - chaseos_obsidian - Review Queue",
            "ui_automation_text": "",
        },
        termination={"terminated": True},
        require_nonblank=True,
        min_unique_colors=8,
        max_dominant_ratio=0.995,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is True
    assert checks["screenshot_studio_content_sentinel"]["ok"] is True
    assert report["screenshot"]["studio_content_sentinel"]["matched_groups"] == [
        ["chaseos studio"],
        ["studio shell"],
        ["review queue"],
    ]


def test_packaged_visual_qa_blocks_nonblank_capture_without_studio_content_sentinel(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "visual.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        colors = [
            b"\xff\xff\xff",
            b"\x00\x00\x00",
            b"\x38\xbd\xf8",
            b"\x63\x66\xf1",
            b"\x22\xc5\x5e",
            b"\xef\x44\x44",
            b"\xfa\xcc\x15",
            b"\xa8\x55\xf7",
        ]
        path = Path(kwargs["screenshot_path"])
        _write_png(path, 70, 40, colors * 350)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": path.stat().st_size,
            "capture_method": "print_window",
            "ui_automation_text": "Antigravity Explorer File Edit Selection Terminal docs/VentureOps_goal.md",
        }

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    assert report["ok"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["screenshot_nonblank"]["ok"] is True
    assert checks["screenshot_studio_content_sentinel"]["ok"] is False
    assert report["screenshot"]["studio_content_sentinel"]["ok"] is False
    assert report["next_recommended_pass"] == "pass10b-native-window-content-sentinel-diagnostic"
    assert fake_process.terminated is True


def test_packaged_visual_qa_blocks_developer_facing_visible_copy(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "visual-dev-copy.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        colors = [
            b"\xff\xff\xff",
            b"\x00\x00\x00",
            b"\x38\xbd\xf8",
            b"\x63\x66\xf1",
            b"\x22\xc5\x5e",
            b"\xef\x44\x44",
            b"\xfa\xcc\x15",
            b"\xa8\x55\xf7",
        ]
        path = Path(kwargs["screenshot_path"])
        _write_png(path, 70, 40, colors * 350)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": path.stat().st_size,
            "capture_method": "print_window",
            "ui_automation_text": "ChaseOS Studio Product Shell Home Dashboard MVP implementation readonly",
        }

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert checks["screenshot_studio_content_sentinel"]["ok"] is True
    assert checks["screenshot_no_dev_visible_copy"]["ok"] is False
    assert report["screenshot"]["forbidden_visible_copy"]["matches"] == [
        "mvp",
        "dashboard",
        "implementation",
        "readonly",
    ]
    assert "Native UI text contains developer-facing copy: mvp, dashboard, implementation, readonly." in report["blockers"]
    assert report["next_recommended_pass"] == "pass10b-native-window-content-sentinel-diagnostic"
    assert fake_process.terminated is True


def test_packaged_visual_qa_blocks_blank_screenshot(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "blank.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        path = Path(kwargs["screenshot_path"])
        _write_png(path, 70, 40, [b"\xff\xff\xff"] * 2800)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {"ok": True, "width": 900, "height": 700, "size_bytes": path.stat().st_size}

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    assert report["ok"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["screenshot_nonempty"]["ok"] is True
    assert checks["screenshot_nonblank"]["ok"] is False
    assert checks["screenshot_content_area_nonblank"]["ok"] is False
    assert report["screenshot"]["visual_verification"]["reason"] == "blank-or-near-uniform"
    assert fake_process.terminated is True


def test_packaged_visual_qa_blocks_title_bar_only_nonblank_screenshot(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    screenshot = tmp_path / "title-only.png"
    fake_process = FakeProcess(alive=True)

    monkeypatch.setattr(
        visual_qa,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(visual_qa.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(visual_qa.subprocess, "Popen", lambda *args, **kwargs: fake_process)

    def fake_capture(**kwargs):
        width = 100
        height = 140
        title_colors = [
            b"\x20\x20\x20",
            b"\x80\x80\x80",
            b"\xff\xff\xff",
            b"\x38\xbd\xf8",
            b"\x63\x66\xf1",
            b"\x22\xc5\x5e",
            b"\xef\x44\x44",
            b"\xfa\xcc\x15",
        ]
        pixels: list[bytes] = []
        for y in range(height):
            if y < visual_qa.CONTENT_AREA_TOP_SKIP_PIXELS:
                pixels.extend(title_colors[(x + y) % len(title_colors)] for x in range(width))
            else:
                pixels.extend([b"\xff\xff\xff"] * width)
        path = Path(kwargs["screenshot_path"])
        _write_png(path, width, height, pixels)
        path.write_bytes(path.read_bytes() + (b"x" * 2048))
        return {
            "ok": True,
            "width": 900,
            "height": 700,
            "size_bytes": path.stat().st_size,
            "capture_method": "print_window",
            "window_title": "ChaseOS Studio Product Shell - chaseos_obsidian",
        }

    monkeypatch.setattr(visual_qa, "_capture_window_screenshot", fake_capture)

    report = visual_qa.build_packaged_app_visual_qa(
        tmp_path,
        executable_path=exe,
        screenshot_path=screenshot,
        settle_seconds=0.1,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is False
    assert checks["screenshot_nonblank"]["ok"] is True
    assert checks["screenshot_content_area_nonblank"]["ok"] is False
    assert "Native window screenshot content area is blank or near-uniform." in report["blockers"]
    assert report["next_recommended_pass"] == "pass10b-native-window-content-sentinel-diagnostic"
    assert fake_process.terminated is True


def test_packaged_visual_qa_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": "packaged_app_visual_qa_complete",
        "generated_at": "2026-05-04T00:00:00Z",
        "screenshot": {
            "path": ".pytest_tmp_env/studio-packaged-app-visual-qa/visual.png",
            "exists": True,
            "size_bytes": 2048,
            "capture": {"width": 900, "height": 700},
        },
        "checks": [{"name": "window_capture_ok", "ok": True, "detail": "ok"}],
        "authority": {"canonical_mutation_allowed": False},
    }

    evidence = visual_qa.write_visual_qa_evidence(
        tmp_path,
        report,
        evidence_slug="visual-qa-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
    assert evidence["screenshot_path"] == ".pytest_tmp_env/studio-packaged-app-visual-qa/visual.png"


def test_packaged_visual_qa_evidence_writer_rejects_root_outside_vault(tmp_path: Path) -> None:
    report = {
        "ok": False,
        "status": "blocked_packaged_app_visual_qa",
        "generated_at": "2026-05-11T00:00:00Z",
        "screenshot": {"path": "visual.png", "exists": False, "size_bytes": 0},
        "checks": [],
        "authority": {"canonical_mutation_allowed": False},
    }
    outside = tmp_path.parent / "outside-visual-qa-evidence"

    with pytest.raises(ValueError, match="evidence root must stay inside"):
        visual_qa.write_visual_qa_evidence(
            tmp_path,
            report,
            evidence_root=outside,
        )


def test_packaged_visual_qa_evidence_writer_rejects_slug_path_traversal(tmp_path: Path) -> None:
    report = {
        "ok": False,
        "status": "blocked_packaged_app_visual_qa",
        "generated_at": "2026-05-11T00:00:00Z",
        "screenshot": {"path": "visual.png", "exists": False, "size_bytes": 0},
        "checks": [],
        "authority": {"canonical_mutation_allowed": False},
    }

    with pytest.raises(ValueError, match="evidence output must stay inside"):
        visual_qa.write_visual_qa_evidence(
            tmp_path,
            report,
            evidence_root="evidence",
            evidence_slug="../../outside-visual-qa",
        )
    assert (tmp_path / "evidence").exists() is False


def test_packaged_visual_qa_evidence_writer_rejects_slug_escape_from_evidence_root(tmp_path: Path) -> None:
    report = {
        "ok": False,
        "status": "blocked_packaged_app_visual_qa",
        "generated_at": "2026-05-11T00:00:00Z",
        "screenshot": {"path": "visual.png", "exists": False, "size_bytes": 0},
        "checks": [],
        "authority": {"canonical_mutation_allowed": False},
    }

    with pytest.raises(ValueError, match="evidence output must stay inside the evidence root"):
        visual_qa.write_visual_qa_evidence(
            tmp_path,
            report,
            evidence_root="evidence",
            evidence_slug="../vault-local-but-outside-root",
    )
    assert (tmp_path / "evidence").exists() is False
    assert (tmp_path / "vault-local-but-outside-root.json").exists() is False
    assert (tmp_path / "vault-local-but-outside-root.md").exists() is False


def test_packaged_visual_qa_cli_returns_json_error_for_outside_evidence_root(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    from runtime.cli import main as cli_main

    outside = tmp_path.parent / "outside-cli-visual-qa-evidence"

    def fake_build_packaged_app_visual_qa(*_args, **_kwargs):
        return {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "generated_at": "2026-05-11T00:00:00Z",
            "screenshot": {"path": "visual.png", "exists": False, "size_bytes": 0},
            "checks": [],
            "authority": {"canonical_mutation_allowed": False},
        }

    monkeypatch.setattr(
        visual_qa,
        "build_packaged_app_visual_qa",
        fake_build_packaged_app_visual_qa,
    )
    args = argparse.Namespace(
        vault_root=str(tmp_path),
        executable_path=None,
        screenshot_path="visual.png",
        settle_seconds=0.1,
        window_timeout_seconds=0.1,
        terminate_timeout_seconds=0.1,
        allow_blank_screenshot=False,
        min_unique_colors=8,
        max_dominant_ratio=0.995,
        write_evidence=True,
        evidence_slug="cli-boundary",
        evidence_root=str(outside),
        output_json=True,
    )

    exit_code = cli_main.cmd_studio_packaged_app_visual_qa(args)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["ok"] is False
    assert "evidence root must stay inside" in payload["error"]
    assert outside.exists() is False


def test_packaged_visual_qa_cli_rejects_outside_evidence_root_before_default_screenshot(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    from runtime.cli import main as cli_main

    outside = tmp_path.parent / "outside-cli-default-screenshot-evidence"

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("build_packaged_app_visual_qa should not run for outside evidence root")

    monkeypatch.setattr(
        visual_qa,
        "build_packaged_app_visual_qa",
        fail_if_called,
    )
    args = argparse.Namespace(
        vault_root=str(tmp_path),
        executable_path=None,
        screenshot_path=None,
        settle_seconds=0.1,
        window_timeout_seconds=0.1,
        terminate_timeout_seconds=0.1,
        allow_blank_screenshot=False,
        min_unique_colors=8,
        max_dominant_ratio=0.995,
        write_evidence=True,
        evidence_slug="cli-default-screenshot-boundary",
        evidence_root=str(outside),
        output_json=True,
    )

    exit_code = cli_main.cmd_studio_packaged_app_visual_qa(args)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["ok"] is False
    assert "evidence root must stay inside" in payload["error"]
    assert outside.exists() is False


def test_packaged_visual_qa_parser_exposes_nonblank_flags() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "packaged-app-visual-qa",
            "--initial-hash",
            "#/chat",
            "--all-pages",
            "--screenshot-root",
            "runtime-dirs/screens",
            "--webview2-user-data-root",
            "runtime-dirs/webview2",
            "--temp-root",
            "runtime-dirs/temp",
            "--allow-external-runtime-dirs",
            "--allow-blank-screenshot",
            "--min-unique-colors",
            "12",
            "--max-dominant-ratio",
            "0.9",
        ]
    )

    assert args.allow_blank_screenshot is True
    assert args.initial_hash == "#/chat"
    assert args.all_pages is True
    assert args.screenshot_root == "runtime-dirs/screens"
    assert args.webview2_user_data_root == "runtime-dirs/webview2"
    assert args.temp_root == "runtime-dirs/temp"
    assert args.allow_external_runtime_dirs is True
    assert args.min_unique_colors == 12
    assert args.max_dominant_ratio == 0.9
