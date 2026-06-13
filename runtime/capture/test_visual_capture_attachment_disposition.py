from __future__ import annotations

import json
from pathlib import Path

from runtime.capture.visual_capture import (
    ATTACHMENT_DELETE_CONFIRMATION,
    ATTACHMENT_DISPOSITION_POLICY_ID,
    VisualCaptureAttachment,
    build_attachment_disposition_policy,
    cleanup_capture_attachments,
    update_capture_attachment_disposition,
)


def _attachment() -> VisualCaptureAttachment:
    return VisualCaptureAttachment(
        attachment_id="screenshot-1",
        filename="screenshot.png",
        relative_path="03_INPUTS/00_QUARANTINE/Sources/_attachments/vcmi/screenshot.png",
        mime_type="image/png",
        sha256="a" * 64,
        size_bytes=123,
        redaction_status="operator-review-required",
    )


def test_attachment_disposition_policy_exposes_guarded_studio_controls() -> None:
    policy = build_attachment_disposition_policy([_attachment()], review_status="pending-review")

    assert policy["policy_id"] == ATTACHMENT_DISPOSITION_POLICY_ID
    assert policy["status"] == "metadata_policy_only"
    assert policy["applicable"] is True
    assert policy["attachment_count"] == 1
    assert policy["default_disposition"] == "retain-until-downstream-review"
    assert "retain" in policy["supported_dispositions"]
    assert "needs-redaction" in policy["supported_dispositions"]
    assert "delete-requested" in policy["supported_dispositions"]
    assert policy["runtime_delete_allowed"] is False
    assert policy["studio_delete_controls_allowed"] is True
    assert policy["cleanup_executor_available"] is True
    assert policy["cleanup_requires_exact_operator_confirmation"] is True
    assert policy["operator_decision_required_for_delete"] is True
    assert policy["attachments"][0]["runtime_delete_allowed"] is False
    assert "ambient_attachment_delete" in policy["forbidden_effects"]


def test_attachment_disposition_delete_requested_is_metadata_only() -> None:
    policy = build_attachment_disposition_policy(
        [_attachment()],
        review_status="rejected",
        requested_disposition="delete-requested",
    )

    assert policy["default_disposition"] == "delete-requested"
    assert policy["delete_request_status"] == "metadata_only_requested"
    assert policy["attachments"][0]["delete_request_status"] == "metadata_only_requested"
    assert policy["runtime_delete_allowed"] is False
    assert policy["authority"]["runtime_delete_allowed"] is False


def test_attachment_disposition_policy_not_applicable_without_attachments() -> None:
    policy = build_attachment_disposition_policy([], review_status="reviewed")

    assert policy["applicable"] is False
    assert policy["attachment_count"] == 0
    assert policy["default_disposition"] == "not-applicable"
    assert policy["runtime_delete_allowed"] is False


def test_attachment_disposition_update_and_cleanup_delete_only_quarantine_copy(tmp_path: Path) -> None:
    content = _write_capture_with_attachment(tmp_path)
    attachment_path = (
        tmp_path
        / "03_INPUTS"
        / "00_QUARANTINE"
        / "Sources"
        / "_attachments"
        / "capture-1"
        / "screenshot.png"
    )
    assert attachment_path.exists()

    update = update_capture_attachment_disposition(
        tmp_path,
        content,
        requested_disposition="delete-requested",
        reviewed_by="unit",
        review_note="delete copied proof attachment",
    )

    assert update["ok"] is True
    assert update["requested_disposition"] == "delete-requested"
    assert update["write_performed"] is True
    assert attachment_path.exists()

    missing_confirmation = cleanup_capture_attachments(
        tmp_path,
        content,
        operator_confirmed=True,
        confirmation_phrase="wrong",
    )
    assert missing_confirmation["ok"] is False
    assert missing_confirmation["blockers"] == ["exact_delete_confirmation_required"]
    assert attachment_path.exists()

    cleanup = cleanup_capture_attachments(
        tmp_path,
        content,
        operator_confirmed=True,
        confirmation_phrase=ATTACHMENT_DELETE_CONFIRMATION,
    )

    assert cleanup["ok"] is True
    assert cleanup["deleted_count"] == 1
    assert cleanup["write_performed"] is True
    assert not attachment_path.exists()
    sidecar = json.loads(content.with_suffix(".meta.json").read_text(encoding="utf-8"))
    visual = sidecar["extra_metadata"]["visual_capture"]
    assert visual["attachment_cleanup_status"] == "deleted"


def _write_capture_with_attachment(root: Path) -> Path:
    capture_dir = root / "03_INPUTS" / "00_QUARANTINE" / "Sources"
    attachment_dir = capture_dir / "_attachments" / "capture-1"
    attachment_dir.mkdir(parents=True, exist_ok=True)
    attachment = attachment_dir / "screenshot.png"
    attachment.write_bytes(b"png")
    content = capture_dir / "capture.md"
    content.write_text("# Capture\n", encoding="utf-8")
    sidecar = content.with_suffix(".meta.json")
    packet = content.with_suffix(".visual_capture.json")
    attachment_row = {
        "attachment_id": "screenshot-1",
        "filename": "screenshot.png",
        "relative_path": "03_INPUTS/00_QUARANTINE/Sources/_attachments/capture-1/screenshot.png",
        "mime_type": "image/png",
        "sha256": "a" * 64,
        "size_bytes": 3,
        "redaction_status": "operator-review-required",
    }
    sidecar.write_text(
        json.dumps(
            {
                "title": "Attachment Capture",
                "content_filename": "capture.md",
                "review_status": "pending-review",
                "extra_metadata": {
                    "visual_capture": {
                        "capture_id": "capture-1",
                        "review_status": "pending-review",
                        "attachments": [attachment_row],
                        "attachment_disposition_policy": build_attachment_disposition_policy(
                            [attachment_row],
                            review_status="pending-review",
                        ),
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    packet.write_text(
        json.dumps(
            {
                "capture_id": "capture-1",
                "routing": {"review_status": "pending-review"},
                "attachments": [attachment_row],
                "provenance": {"transformation_chain": []},
            }
        ),
        encoding="utf-8",
    )
    return content
