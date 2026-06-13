"""Tests for acquisition connector health telemetry."""

from __future__ import annotations

import sys
import shutil
import uuid
from email.message import EmailMessage
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.acquisition.connector_health import (  # noqa: E402
    ConnectorHealthEvent,
    append_connector_health_event,
    connector_health_path,
    load_connector_health_events,
    safe_error_preview,
    summarize_connector_health,
)
from runtime.acquisition.live_sources import LiveQuerySpec, run_live_captures  # noqa: E402
from runtime.acquisition.adapters.email_adapter import EmailFetchSpec, acquire_email_messages  # noqa: E402
from runtime.acquisition.adapters.google_adapter import (  # noqa: E402
    GoogleDocSpec,
    GoogleDriveFolderSpec,
    acquire_google_doc,
    acquire_google_drive_folder,
)
from runtime.acquisition.adapters.rss_live_adapter import RssFeedSpec, acquire_rss_feed  # noqa: E402
from runtime.acquisition.adapters.web_scrape_adapter import WebPageSpec, acquire_web_page  # noqa: E402


def _make_vault() -> Path:
    vault = _VAULT_ROOT / ".codex_tmp_test" / "acquisition-connector-health" / uuid.uuid4().hex / "vault"
    vault.mkdir(parents=True)
    return vault


def _cleanup_vault(vault: Path) -> None:
    root = (_VAULT_ROOT / ".codex_tmp_test" / "acquisition-connector-health").resolve()
    target = vault.parent.resolve()
    if target.parent == root:
        shutil.rmtree(target, ignore_errors=True)


def _provider_state_ledger_path(vault: Path) -> Path:
    return vault / "runtime" / "providers" / "state" / "provider_state_events.jsonl"


def _make_email_bytes(subject: str, body: str) -> bytes:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "desk@example.com"
    msg["To"] = "operator@example.com"
    msg["Date"] = "Tue, 28 Apr 2026 08:00:00 +0000"
    msg["Message-ID"] = f"<{uuid.uuid4().hex}@example.com>"
    msg.set_content(body)
    return msg.as_bytes()


def test_connector_health_event_append_load_and_summary() -> None:
    vault = _make_vault()
    event = ConnectorHealthEvent(
        event_type="connector.capture_failed",
        connector_id="perplexity",
        provider="perplexity",
        source_id="test-perplexity",
        surface="runtime.acquisition.live_sources",
        failure_reason="credential_missing",
        error_type="PerplexityCredentialError",
        error_preview="PERPLEXITY_API_KEY environment variable not set",
    )

    try:
        persisted = append_connector_health_event(vault, event)
        events = load_connector_health_events(vault)
        summary = summarize_connector_health(vault)

        assert connector_health_path(vault).exists()
        assert persisted["status"] == "failed"
        assert [item["event_type"] for item in events] == ["connector.capture_failed"]
        assert summary["event_count"] == 1
        assert summary["status_counts"]["failed"] == 1
        assert summary["connectors"]["perplexity"]["latest_event"]["failure_reason"] == "credential_missing"
    finally:
        _cleanup_vault(vault)


def test_safe_error_preview_redacts_common_api_key_shapes() -> None:
    preview = safe_error_preview(
        "failed with Bearer pplx-bearer-token and pplx-direct-token plus xai-direct-token and test-key-direct-token"
    )

    assert "pplx-bearer-token" not in preview
    assert "pplx-direct-token" not in preview
    assert "xai-direct-token" not in preview
    assert "test-key-direct-token" not in preview
    assert preview.count("[redacted]") == 4


def test_run_live_captures_records_perplexity_success() -> None:
    vault = _make_vault()
    spec = LiveQuerySpec(
        source_id="per-success",
        provider="perplexity",
        query="market context",
        display_name="Perplexity Success",
        source_class="perplexity_digest",
    )

    try:
        packet = SimpleNamespace(content="Perplexity captured market context.")
        with patch("runtime.capture.connectors.perplexity_connector.capture_from_perplexity", return_value=packet):
            staged = run_live_captures([spec], vault, staging_subdir="test")

        events = load_connector_health_events(vault)
        assert len(staged) == 1
        assert len(events) == 1
        assert events[0]["event_type"] == "connector.capture_succeeded"
        assert events[0]["connector_id"] == "perplexity"
        assert events[0]["staging_path"] == staged[0].relative_path
    finally:
        _cleanup_vault(vault)


def test_run_live_captures_records_perplexity_credential_failure_without_provider_ledger(
    monkeypatch,
) -> None:
    vault = _make_vault()
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    spec = LiveQuerySpec(
        source_id="per-fail",
        provider="perplexity",
        query="market context",
        display_name="Perplexity Failure",
        source_class="perplexity_digest",
    )

    try:
        staged = run_live_captures([spec], vault, staging_subdir="test")
        events = load_connector_health_events(vault)

        assert staged == []
        assert [event["event_type"] for event in events] == ["connector.capture_failed"]
        assert events[0]["failure_reason"] == "credential_missing"
        assert events[0]["error_type"] == "PerplexityCredentialError"
        assert not (vault / "runtime" / "providers" / "state" / "provider_state_events.jsonl").exists()
    finally:
        _cleanup_vault(vault)


def test_run_live_captures_records_grok_credential_failure(monkeypatch) -> None:
    vault = _make_vault()
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    spec = LiveQuerySpec(
        source_id="grok-fail",
        provider="grok",
        query="market narrative",
        display_name="Grok Failure",
        source_class="grok_digest",
    )

    try:
        staged = run_live_captures([spec], vault, staging_subdir="test")
        events = load_connector_health_events(vault)

        assert staged == []
        assert [event["event_type"] for event in events] == ["connector.capture_failed"]
        assert events[0]["connector_id"] == "grok"
        assert events[0]["failure_reason"] == "credential_missing"
        assert events[0]["error_type"] == "GrokCredentialError"
    finally:
        _cleanup_vault(vault)


def test_run_live_captures_records_unknown_provider_skip() -> None:
    vault = _make_vault()
    spec = LiveQuerySpec(
        source_id="unknown-source",
        provider="unknown-provider",
        query="q",
        display_name="Unknown",
    )

    try:
        staged = run_live_captures([spec], vault, staging_subdir="test")
        events = load_connector_health_events(vault)

        assert staged == []
        assert [event["event_type"] for event in events] == ["connector.capture_skipped"]
        assert events[0]["connector_id"] == "unknown-provider"
        assert events[0]["failure_reason"] == "unknown_provider"
    finally:
        _cleanup_vault(vault)


def test_acquire_rss_feed_records_connector_health_success() -> None:
    vault = _make_vault()
    spec = RssFeedSpec(
        source_id="rss-success",
        url="https://example.com/feed.xml",
        display_name="Example RSS",
    )
    rss_xml = """<?xml version="1.0"?>
<rss><channel><title>Example Feed</title><item><title>Market Update</title><link>https://example.com/a</link><description>BTC moved.</description></item></channel></rss>"""

    try:
        with patch("runtime.capture.connectors.rss_connector.fetch_feed", return_value=rss_xml):
            staged = acquire_rss_feed(spec, vault, staging_subdir="test", plan_id="plan-rss")

        events = load_connector_health_events(vault)
        assert staged is not None
        assert [event["event_type"] for event in events] == ["connector.capture_succeeded"]
        assert events[0]["connector_id"] == "rss"
        assert events[0]["staging_path"] == staged.relative_path
        assert events[0]["data"]["item_count"] == 1
        assert not _provider_state_ledger_path(vault).exists()
    finally:
        _cleanup_vault(vault)


def test_acquire_rss_feed_records_connector_health_failure() -> None:
    vault = _make_vault()
    spec = RssFeedSpec(
        source_id="rss-fail",
        url="https://example.com/feed.xml",
        display_name="Example RSS",
    )

    try:
        with patch("runtime.capture.connectors.rss_connector.fetch_feed", side_effect=Exception("network timeout")):
            staged = acquire_rss_feed(spec, vault, staging_subdir="test")

        events = load_connector_health_events(vault)
        assert staged is None
        assert [event["event_type"] for event in events] == ["connector.capture_failed"]
        assert events[0]["connector_id"] == "rss"
        assert events[0]["failure_reason"] == "network_error"
    finally:
        _cleanup_vault(vault)


def test_acquire_web_page_records_connector_health_success() -> None:
    vault = _make_vault()
    spec = WebPageSpec(
        source_id="web-success",
        url="https://example.com/page",
        display_name="Example Page",
    )
    html = "<html><head><title>Example Page</title></head><body><h1>Markets</h1><p>Risk assets rallied.</p></body></html>"

    try:
        with patch("runtime.acquisition.adapters.web_scrape_adapter._fetch_html", return_value=html):
            staged = acquire_web_page(spec, vault, staging_subdir="test", plan_id="plan-web")

        events = load_connector_health_events(vault)
        assert staged is not None
        assert [event["event_type"] for event in events] == ["connector.capture_succeeded"]
        assert events[0]["connector_id"] == "web_scrape"
        assert events[0]["provider"] == "web"
        assert events[0]["staging_path"] == staged.relative_path
    finally:
        _cleanup_vault(vault)


def test_acquire_web_page_records_empty_content_skip() -> None:
    vault = _make_vault()
    spec = WebPageSpec(
        source_id="web-empty",
        url="https://example.com/empty",
        display_name="Empty Page",
    )

    try:
        with patch("runtime.acquisition.adapters.web_scrape_adapter._fetch_html", return_value="<html><body></body></html>"):
            staged = acquire_web_page(spec, vault, staging_subdir="test")

        events = load_connector_health_events(vault)
        assert staged is None
        assert [event["event_type"] for event in events] == ["connector.capture_skipped"]
        assert events[0]["connector_id"] == "web_scrape"
        assert events[0]["failure_reason"] == "empty_content"
    finally:
        _cleanup_vault(vault)


def test_acquire_email_messages_records_credential_failure() -> None:
    vault = _make_vault()
    spec = EmailFetchSpec(source_id="email-fail", display_name="Email Digest")

    try:
        with patch.dict("os.environ", {}, clear=True):
            staged = acquire_email_messages(spec, vault, staging_subdir="test")

        events = load_connector_health_events(vault)
        assert staged is None
        assert [event["event_type"] for event in events] == ["connector.capture_failed"]
        assert events[0]["connector_id"] == "email_imap"
        assert events[0]["failure_reason"] == "credential_missing"
    finally:
        _cleanup_vault(vault)


def test_acquire_email_messages_records_connector_health_success() -> None:
    vault = _make_vault()
    spec = EmailFetchSpec(source_id="email-success", display_name="Email Digest")
    mock_imap = MagicMock()
    mock_imap.__enter__ = MagicMock(return_value=mock_imap)
    mock_imap.__exit__ = MagicMock(return_value=False)
    mock_imap.login.return_value = ("OK", [b"Logged in"])
    mock_imap.select.return_value = ("OK", [b"1"])
    mock_imap.search.return_value = ("OK", [b"1"])
    mock_imap.fetch.return_value = ("OK", [(b"1", _make_email_bytes("Daily Brief", "Crypto market context."))])

    try:
        with patch.dict("os.environ", {"IMAP_USER": "desk@example.com", "IMAP_PASSWORD": "app-pass"}, clear=True):
            with patch("imaplib.IMAP4_SSL", return_value=mock_imap):
                staged = acquire_email_messages(spec, vault, staging_subdir="test", plan_id="plan-email")

        events = load_connector_health_events(vault)
        assert staged is not None
        assert [event["event_type"] for event in events] == ["connector.capture_succeeded"]
        assert events[0]["connector_id"] == "email_imap"
        assert events[0]["staging_path"] == staged.relative_path
        assert events[0]["data"]["message_count"] == 1
    finally:
        _cleanup_vault(vault)


def test_acquire_google_doc_records_connector_health_success() -> None:
    vault = _make_vault()
    spec = GoogleDocSpec(source_id="gdoc-success", doc_id="doc123", display_name="Trade Thesis")

    try:
        with patch("runtime.acquisition.adapters.google_adapter._fetch_url", return_value=b"Trade thesis text."):
            staged = acquire_google_doc(spec, vault, staging_subdir="test", plan_id="plan-gdoc")

        events = load_connector_health_events(vault)
        assert staged is not None
        assert [event["event_type"] for event in events] == ["connector.capture_succeeded"]
        assert events[0]["connector_id"] == "google_docs"
        assert events[0]["provider"] == "google"
        assert events[0]["staging_path"] == staged.relative_path
    finally:
        _cleanup_vault(vault)


def test_acquire_google_doc_records_private_credential_failure() -> None:
    vault = _make_vault()
    spec = GoogleDocSpec(
        source_id="gdoc-private",
        doc_id="doc-private",
        display_name="Private Doc",
        is_public=False,
    )

    try:
        with patch.dict("os.environ", {}, clear=True):
            staged = acquire_google_doc(spec, vault, staging_subdir="test")

        events = load_connector_health_events(vault)
        assert staged is None
        assert [event["event_type"] for event in events] == ["connector.capture_failed"]
        assert events[0]["connector_id"] == "google_docs"
        assert events[0]["failure_reason"] == "credential_missing"
    finally:
        _cleanup_vault(vault)


def test_acquire_google_drive_folder_records_missing_credentials() -> None:
    vault = _make_vault()
    spec = GoogleDriveFolderSpec(source_id="gdrive-fail", folder_id="folder123", display_name="Drive Folder")

    try:
        with patch.dict("os.environ", {}, clear=True):
            staged = acquire_google_drive_folder(spec, vault, staging_subdir="test")

        events = load_connector_health_events(vault)
        assert staged is None
        assert [event["event_type"] for event in events] == ["connector.capture_failed"]
        assert events[0]["connector_id"] == "google_drive"
        assert events[0]["failure_reason"] == "credential_missing"
    finally:
        _cleanup_vault(vault)


def test_acquire_google_drive_folder_records_connector_health_success() -> None:
    vault = _make_vault()
    spec = GoogleDriveFolderSpec(source_id="gdrive-success", folder_id="folder123", display_name="Drive Folder")
    files = [{"id": "doc1", "name": "Drive Doc", "mimeType": "application/vnd.google-apps.document", "modifiedTime": "2026-04-28T08:00:00Z"}]

    try:
        with patch.dict("os.environ", {"GOOGLE_OAUTH_TOKEN": "fake-token"}, clear=True):
            with patch("runtime.acquisition.adapters.google_adapter.list_drive_files", return_value=files):
                with patch("runtime.acquisition.adapters.google_adapter._fetch_url", return_value=b"Drive doc text."):
                    staged = acquire_google_drive_folder(spec, vault, staging_subdir="test", plan_id="plan-gdrive")

        events = load_connector_health_events(vault)
        assert staged is not None
        assert [event["event_type"] for event in events] == ["connector.capture_succeeded"]
        assert events[0]["connector_id"] == "google_drive"
        assert events[0]["staging_path"] == staged.relative_path
        assert events[0]["data"]["exported_file_count"] == 1
    finally:
        _cleanup_vault(vault)
