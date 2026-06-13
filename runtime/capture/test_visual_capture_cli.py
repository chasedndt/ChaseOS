from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

from runtime.cli.main import main as cli_main


PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15"
    "c4890000000d49444154789c6360000002000100ffff03000006000557bfab"
    "d40000000049454e44ae426082"
)


def _run_cli(argv: list[str]) -> tuple[int, dict, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = cli_main(argv)
    return exit_code, json.loads(stdout.getvalue()), stderr.getvalue()


def _run_cli_text(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            exit_code = cli_main(argv)
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 1
    return exit_code, stdout.getvalue(), stderr.getvalue()


def test_capture_markdown_help_uses_product_language() -> None:
    capture_code, capture_help, capture_stderr = _run_cli_text(["capture", "--help"])
    markdown_code, markdown_help, markdown_stderr = _run_cli_text(["capture", "markdown", "--help"])
    acquisition_code, acquisition_help, acquisition_stderr = _run_cli_text(["acquisition", "--help"])

    assert (capture_code, markdown_code, acquisition_code) == (0, 0, 0)
    assert capture_stderr == ""
    assert markdown_stderr == ""
    assert acquisition_stderr == ""

    combined_help = " ".join("\n".join([capture_help, markdown_help, acquisition_help]).split())
    assert "Capture to Markdown raw intake" in combined_help
    assert "Update governed Capture to Markdown raw-quarantine review state without promotion" in combined_help
    assert "Agent Orchestration Runtime dispatch readiness" in combined_help
    assert "Source Intelligence Core ingestion" in combined_help
    assert "Visual Capture to Markdown" not in combined_help
    assert "VCMI" not in combined_help
    assert "AOR" not in combined_help
    assert "SIC" not in combined_help


def _write_png(vault_root: Path, relative_path: str = "07_LOGS/Operator-Screenshots/local/default/screenshot.png") -> Path:
    target = vault_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PNG_BYTES)
    return target


def _write_fake_local_text_engine(vault_root: Path, text: str) -> str:
    script = vault_root / "runtime" / "capture" / "fake-local-text-engine.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "from __future__ import annotations\n"
        "import json\n"
        "import sys\n"
        "if len(sys.argv) < 2:\n"
        "    raise SystemExit(2)\n"
        f"print(json.loads({json.dumps(text)!r}))\n",
        encoding="utf-8",
    )
    return json.dumps([sys.executable, str(script)])


def test_capture_markdown_preview_json_envelope_performs_no_writes(tmp_path: Path) -> None:
    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "preview",
            "--title",
            "CLI Preview",
            "--text",
            "Visible source text for a no-write preview.",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "capture.markdown.preview"
    result = payload["result"]
    assert result["status"] == "preview_only"
    assert result["write_performed"] is False
    assert result["save_allowed"] is True
    assert result["authority"]["raw_ingestion_write"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_capture_markdown_save_json_envelope_writes_only_quarantine(tmp_path: Path) -> None:
    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "save",
            "--title",
            "CLI Save",
            "--text",
            "Visible source text for quarantine only.",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "capture.markdown.save"
    result = payload["result"]
    assert result["status"] == "raw_ingested"
    assert result["write_performed"] is True
    assert result["authority"]["raw_ingestion_write"] is True
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert result["authority"]["provider_call_allowed"] is False
    assert Path(result["content_path"]).exists()
    assert Path(result["sidecar_path"]).exists()
    assert Path(result["visual_capture_packet_path"]).exists()
    assert "03_INPUTS" in result["content_path"]
    assert "00_QUARANTINE" in result["content_path"]
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "runtime" / "source_intelligence").exists()
    assert not (tmp_path / "07_LOGS" / "Workflow-Proofs").exists()


def test_capture_markdown_recent_reads_visual_capture_sidecars_without_writes(tmp_path: Path) -> None:
    save_code, save_payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "save",
            "--title",
            "CLI Recent Source",
            "--text",
            "A saved visual capture that should appear in recent rows.",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert save_code == 0, save_payload

    recent_code, recent_payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "recent",
            "--limit",
            "5",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert recent_code == 0
    assert recent_payload["ok"] is True
    assert recent_payload["action"] == "capture.markdown.recent"
    result = recent_payload["result"]
    assert result["read_only"] is True
    assert result["write_performed"] is False
    assert result["count"] == 1
    assert result["recent_captures"][0]["title"] == "CLI Recent Source"
    assert result["recent_captures"][0]["canonical_status"] == "not_promoted"


def test_capture_markdown_review_json_envelope_updates_review_state_only(tmp_path: Path) -> None:
    save_code, save_payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "save",
            "--title",
            "CLI Review Source",
            "--text",
            "A saved visual capture that should be operator reviewed.",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert save_code == 0, save_payload
    saved = save_payload["result"]

    review_code, review_payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "review",
            saved["sidecar_path"],
            "--decision",
            "reviewed",
            "--reviewed-by",
            "operator",
            "--review-note",
            "checked",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert review_code == 0
    assert review_payload["ok"] is True
    assert review_payload["action"] == "capture.markdown.review"
    result = review_payload["result"]
    assert result["status"] == "review_state_updated"
    assert result["old_status"] == "pending-review"
    assert result["new_status"] == "reviewed"
    assert result["content_write_performed"] is False
    assert result["sidecar_write_performed"] is True
    assert result["authority"]["canonical_mutation_allowed"] is False
    sidecar = json.loads(Path(saved["sidecar_path"]).read_text(encoding="utf-8"))
    packet = json.loads(Path(saved["visual_capture_packet_path"]).read_text(encoding="utf-8"))
    assert sidecar["quarantine_status"] == "reviewed"
    assert sidecar["extra_metadata"]["visual_capture"]["review_status"] == "reviewed"
    assert packet["routing"]["review_status"] == "reviewed"
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "runtime" / "source_intelligence").exists()


def test_capture_markdown_save_blocks_secret_like_text_without_writes(tmp_path: Path) -> None:
    raw_secret = "api_key=test-key-abcdefghijklmnopqrstuvwxyz123456"
    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "save",
            "--title",
            "Secret Bearing CLI Capture",
            "--text",
            f"Visible config {raw_secret}",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "capture.markdown.save"
    result = payload["result"]
    assert result["status"] == "blocked_secret_like"
    assert result["write_performed"] is False
    assert result["blockers"] == ["secret_or_credential_indicator_present"]
    assert raw_secret not in result["markdown"]
    assert not (tmp_path / "03_INPUTS" / "00_QUARANTINE").exists()


def test_capture_markdown_preview_accepts_controlled_browser_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "07_LOGS" / "Browser-Runs" / "local" / "default" / "controlled.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        "<html><head><title>Controlled CLI</title></head><body><p>CLI controlled text.</p></body></html>",
        encoding="utf-8",
    )

    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "preview",
            "--title",
            "Controlled CLI",
            "--from-controlled-html",
            "07_LOGS/Browser-Runs/local/default/controlled.html",
            "--url",
            "https://example.com/controlled",
            "--allowed-origin",
            "https://example.com",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 0
    assert payload["ok"] is True
    result = payload["result"]
    assert result["status"] == "preview_only"
    assert result["write_performed"] is False
    assert result["packet"]["capture_method"] == "controlled_browser_dom"
    assert result["packet"]["source"]["declared_source"] == "07_LOGS/Browser-Runs/local/default/controlled.html"
    assert "CLI controlled text." in result["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_capture_markdown_preview_blocks_unconfined_controlled_browser_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "captures" / "unconfined.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("<html><body><p>Unconfined.</p></body></html>", encoding="utf-8")

    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "preview",
            "--title",
            "Unconfined CLI",
            "--from-controlled-html",
            "captures/unconfined.html",
            "--url",
            "https://example.com/unconfined",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["result"]["status"] == "preview_failed"
    assert payload["result"]["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_capture_markdown_preview_accepts_screenshot_attachment_without_ocr(tmp_path: Path) -> None:
    _write_png(tmp_path)

    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "preview",
            "--title",
            "Screenshot CLI",
            "--from-screenshot",
            "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 0
    assert payload["ok"] is True
    result = payload["result"]
    assert result["status"] == "preview_only"
    assert result["write_performed"] is False
    assert result["packet"]["capture_method"] == "screenshot_attachment_import"
    assert result["packet"]["quality"]["extraction_status"] == "attachment_only"
    assert result["packet"]["quality"]["confidence"] == "screenshot_attachment_no_ocr"
    assert "ocr_not_performed" in result["packet"]["quality"]["extraction_warnings"]
    assert "no_cloud_ocr" in result["packet"]["quality"]["extraction_warnings"]
    assert result["packet"]["attachments"][0]["mime_type"] == "image/png"
    assert result["authority"]["provider_call_allowed"] is False
    assert "screenshots:" in result["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_capture_markdown_preview_accepts_screenshot_text_extraction(tmp_path: Path) -> None:
    _write_png(tmp_path)
    command = _write_fake_local_text_engine(tmp_path, "CLI extracted image text.")

    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "preview",
            "--title",
            "Screenshot Text CLI",
            "--from-screenshot-text",
            "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            "--local-optical-character-recognition-command",
            command,
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 0
    assert payload["ok"] is True
    result = payload["result"]
    assert result["status"] == "preview_only"
    assert result["write_performed"] is False
    assert result["packet"]["capture_method"] == "screenshot_local_text_extraction"
    assert result["packet"]["quality"]["extraction_status"] == "text_extracted"
    assert result["packet"]["quality"]["confidence"] == "local_optical_character_recognition"
    assert "local_optical_character_recognition_performed" in result["packet"]["quality"]["extraction_warnings"]
    assert "CLI extracted image text." in result["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_capture_markdown_preview_blocks_unconfined_screenshot_attachment(tmp_path: Path) -> None:
    _write_png(tmp_path, "captures/screenshot.png")

    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "preview",
            "--title",
            "Unconfined Screenshot",
            "--from-screenshot",
            "captures/screenshot.png",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["result"]["status"] == "preview_failed"
    assert payload["result"]["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_capture_markdown_save_copies_screenshot_attachment_into_quarantine(tmp_path: Path) -> None:
    _write_png(tmp_path)

    exit_code, payload, _stderr = _run_cli(
        [
            "capture",
            "markdown",
            "save",
            "--title",
            "Screenshot CLI Save",
            "--from-screenshot",
            "07_LOGS/Operator-Screenshots/local/default/screenshot.png",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    assert exit_code == 0
    assert payload["ok"] is True
    result = payload["result"]
    assert result["status"] == "raw_ingested"
    assert result["write_performed"] is True
    attachment_path = result["packet"]["attachments"][0]["relative_path"]
    assert attachment_path.startswith("03_INPUTS/00_QUARANTINE/Sources/_attachments/")
    assert (tmp_path / attachment_path).exists()
    sidecar = json.loads(Path(result["sidecar_path"]).read_text(encoding="utf-8"))
    vc_meta = sidecar["extra_metadata"]["visual_capture"]
    assert vc_meta["attachments"][0]["relative_path"] == attachment_path
    assert "screenshot_attachment_copied_to_quarantine" in vc_meta["extraction_warnings"]
    assert "screenshot_attachment_retention_review_required" in vc_meta["extraction_warnings"]
    policy = result["attachment_review_policy"]
    assert policy["storage_status"] == "copied_to_quarantine"
    assert policy["retention_status"] == "retain_until_operator_review"
    assert policy["review_status"] == "pending-review"
    assert policy["runtime_delete_allowed"] is False
    assert policy["delete_allowed_by_runtime"] is False
    assert policy["operator_review_required"] is True
    assert vc_meta["attachment_review_policy"] == policy
