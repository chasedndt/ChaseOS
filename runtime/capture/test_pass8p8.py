"""
test_pass8p8.py — ChaseOS Phase 8 Pass 8
Tests for the Perplexity API connector.

Coverage:
  - Credential loading (_get_api_key missing / empty env var)
  - Empty query validation
  - Successful API call → ContentPacket normalization
  - Default input_class ('digest'), source_platform ('perplexity')
  - capture_method ('api'), origin_kind ('ai-generated')
  - Title derivation from query; truncation; explicit override
  - extra_metadata fields (query, model, citations, citation_count, response_id, usage, capture_method_detail)
  - Citation extraction (present / absent)
  - HTTP error → PerplexityAPIError
  - Non-JSON response → PerplexityAPIError
  - Empty choices → PerplexityAPIError
  - Empty content → placeholder text
  - Semantic hints passed through to ContentPacket
  - Dedup: same content captured twice → duplicate on second
  - CLI `capture perplexity --query "..."` → quarantine write
  - CLI `capture perplexity --json` → JSON output with expected fields
  - CLI credential error → exit code 1
  - Backward compat: `capture file` still works
  - model parameter passed through to API call body

Running: chaseos test capture   (included via cmd_test_capture in main.py)
Manual:  python runtime/capture/test_pass8p8.py
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure vault root is importable
_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.capture.connectors.perplexity_connector import (
    PerplexityAPIError,
    PerplexityCredentialError,
    _get_api_key,
    _make_title,
    capture_from_perplexity,
    query_perplexity,
)
from runtime.capture.content_packet import INPUT_CLASS_DIGEST, INPUT_CLASS_SOURCE


# ── Test runner infrastructure ─────────────────────────────────────────────────

_TESTS: list[tuple[str, object]] = []
_PASS  = 0
_FAIL  = 0
_ERRORS: list[str] = []


def _test(label: str):
    def decorator(fn):
        _TESTS.append((label, fn))
        return fn
    return decorator


def _run_test(label: str, fn) -> None:
    global _PASS, _FAIL
    try:
        fn()
        print("  PASS")
        _PASS += 1
    except AssertionError as exc:
        print(f"  FAIL: {exc}")
        _FAIL += 1
        _ERRORS.append(f"{label}: {exc}")
    except Exception as exc:
        print(f"  ERROR: {type(exc).__name__}: {exc}")
        _FAIL += 1
        _ERRORS.append(f"{label}: {type(exc).__name__}: {exc}")


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


# ── Mock helpers ───────────────────────────────────────────────────────────────

def _make_mock_urlopen(response_dict: dict):
    """
    Return a mock urlopen context-manager that reads response_dict as JSON.

    Usage:
        with patch("urllib.request.urlopen", return_value=_make_mock_urlopen(data)):
            ...
    """
    body = json.dumps(response_dict).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ── Standard response fixture ──────────────────────────────────────────────────

_STANDARD_RESPONSE = {
    "id":    "resp-abc123",
    "model": "sonar",
    "choices": [
        {
            "message": {
                "role":    "assistant",
                "content": (
                    "BTC market structure is characterized by deep liquidity pools "
                    "and institutional ETF flow dynamics that have shifted since Q1 2024. "
                    "Spot ETF approvals created persistent buy-side pressure."
                ),
            }
        }
    ],
    "citations": [
        "https://coindesk.com/btc-etf-flows",
        "https://bloomberg.com/crypto/btc-structure",
    ],
    "usage": {
        "prompt_tokens":     20,
        "completion_tokens": 80,
        "total_tokens":      100,
    },
}

_NO_CITATIONS_RESPONSE = {
    "id":    "resp-nocite",
    "model": "sonar",
    "choices": [
        {
            "message": {
                "role":    "assistant",
                "content": "This is a response without citations.",
            }
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40},
}

_EMPTY_CONTENT_RESPONSE = {
    "id":    "resp-empty",
    "model": "sonar",
    "choices": [{"message": {"role": "assistant", "content": ""}}],
    "usage": {},
}

_NO_CHOICES_RESPONSE = {
    "id":      "resp-nochoices",
    "model":   "sonar",
    "choices": [],
    "usage":   {},
}

_TEST_KEY = "pplx-test-key-12345"
_TEST_QUERY = "BTC market structure and ETF flows"


# ── Tests ──────────────────────────────────────────────────────────────────────

@_test("P8-T01: _get_api_key raises PerplexityCredentialError when env var missing")
def test_missing_env_var():
    env = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        try:
            _get_api_key()
            _assert(False, "should have raised PerplexityCredentialError")
        except PerplexityCredentialError as exc:
            _assert("PERPLEXITY_API_KEY" in str(exc),
                    f"error should mention env var name; got: {exc}")


@_test("P8-T02: _get_api_key raises PerplexityCredentialError when env var is empty string")
def test_empty_env_var():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "   "}):
        try:
            _get_api_key()
            _assert(False, "should have raised PerplexityCredentialError")
        except PerplexityCredentialError:
            pass  # expected


@_test("P8-T03: empty query raises ValueError")
def test_empty_query():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        for bad_query in ("", "   "):
            try:
                capture_from_perplexity(query=bad_query)
                _assert(False, f"should have raised ValueError for query={bad_query!r}")
            except ValueError:
                pass  # expected


@_test("P8-T04: successful API call returns ContentPacket with answer content")
def test_successful_capture():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    _assert("BTC market structure" in packet.content,
            f"content missing expected text; got: {packet.content[:100]!r}")
    _assert(isinstance(packet.content, str), "content should be str")
    _assert(len(packet.content) > 0, "content should not be empty")


@_test("P8-T05: default input_class is 'digest'")
def test_default_input_class():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    _assert(packet.input_class == INPUT_CLASS_DIGEST,
            f"input_class={packet.input_class!r}, expected 'digest'")


@_test("P8-T06: default source_platform is 'perplexity'")
def test_default_source_platform():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    _assert(packet.source_platform == "perplexity",
            f"source_platform={packet.source_platform!r}")


@_test("P8-T07: capture_method is 'api'")
def test_capture_method_api():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    _assert(packet.capture_method == "api",
            f"capture_method={packet.capture_method!r}")


@_test("P8-T08: origin_kind defaults to 'ai-generated'")
def test_origin_kind_default():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    _assert(packet.origin_kind == "ai-generated",
            f"origin_kind={packet.origin_kind!r}")


@_test("P8-T09: title derived from query when --title not provided")
def test_title_from_query():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    _assert(packet.title == _TEST_QUERY,
            f"title={packet.title!r}, expected query text")


@_test("P8-T10: long query title truncated at word boundary")
def test_title_truncation():
    long_query = "This is a very long research query about monetary policy and risk assets " \
                 "in the context of global central bank liquidity cycles and crypto market structure"
    title = _make_title(long_query)
    _assert(len(title) <= 83,
            f"title longer than max (80 + '...'): len={len(title)}, title={title!r}")
    _assert(title.endswith("..."), f"truncated title should end with '...'; got: {title!r}")
    _assert(" " not in title[title.rfind("...") - 1:title.rfind("...")].lstrip(),
            "truncation should occur at word boundary")


@_test("P8-T11: explicit title override respected")
def test_title_override():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(
                query=_TEST_QUERY,
                title="My Custom Research Title",
            )
    _assert(packet.title == "My Custom Research Title",
            f"title={packet.title!r}")


@_test("P8-T12: extra_metadata has all required fields")
def test_extra_metadata_fields():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    em = packet.extra_metadata
    required_fields = [
        "query", "model", "citations", "citation_count",
        "response_id", "usage", "capture_method_detail",
    ]
    for f in required_fields:
        _assert(f in em, f"extra_metadata missing field: {f!r}; keys={list(em.keys())}")
    _assert(em["query"] == _TEST_QUERY, f"query={em['query']!r}")
    _assert(em["capture_method_detail"] == "perplexity-api-chat-completions",
            f"capture_method_detail={em['capture_method_detail']!r}")


@_test("P8-T13: citations extracted when present in API response")
def test_citations_extracted():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    em = packet.extra_metadata
    _assert(isinstance(em["citations"], list), "citations should be a list")
    _assert(em["citation_count"] == 2, f"citation_count={em['citation_count']}")
    _assert("https://coindesk.com/btc-etf-flows" in em["citations"],
            f"expected citation URL missing; citations={em['citations']}")


@_test("P8-T14: absent citations field returns empty list, citation_count 0")
def test_citations_absent():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_NO_CITATIONS_RESPONSE)):
            packet = capture_from_perplexity(query="Fed liquidity")
    em = packet.extra_metadata
    _assert(em["citations"] == [], f"citations should be []; got {em['citations']}")
    _assert(em["citation_count"] == 0, f"citation_count={em['citation_count']}")


@_test("P8-T15: HTTP 401 raises PerplexityAPIError")
def test_http_error_raises_api_error():
    err_body = b'{"error": "invalid_api_key"}'
    http_err = urllib.error.HTTPError(
        _Standard_URL := "https://api.perplexity.ai/chat/completions",
        401,
        "Unauthorized",
        {},
        io.BytesIO(err_body),
    )
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "bad-key"}):
        with patch("urllib.request.urlopen", side_effect=http_err):
            try:
                capture_from_perplexity(query=_TEST_QUERY)
                _assert(False, "should have raised PerplexityAPIError")
            except PerplexityAPIError as exc:
                _assert("401" in str(exc), f"error should mention 401; got: {exc}")


@_test("P8-T16: non-JSON API response raises PerplexityAPIError")
def test_non_json_response():
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"<html>Service Unavailable</html>"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            try:
                capture_from_perplexity(query=_TEST_QUERY)
                _assert(False, "should have raised PerplexityAPIError")
            except PerplexityAPIError as exc:
                _assert("non-JSON" in str(exc) or "JSON" in str(exc),
                        f"error should mention JSON; got: {exc}")


@_test("P8-T17: empty choices in response raises PerplexityAPIError")
def test_empty_choices():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_NO_CHOICES_RESPONSE)):
            try:
                capture_from_perplexity(query=_TEST_QUERY)
                _assert(False, "should have raised PerplexityAPIError")
            except PerplexityAPIError as exc:
                _assert("choices" in str(exc).lower(),
                        f"error should mention choices; got: {exc}")


@_test("P8-T18: empty content produces placeholder text")
def test_empty_content_placeholder():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_EMPTY_CONTENT_RESPONSE)):
            packet = capture_from_perplexity(query=_TEST_QUERY)
    _assert("[Perplexity returned empty content" in packet.content,
            f"expected placeholder; got: {packet.content!r}")
    _assert(len(packet.content) > 0, "content should not be empty string")


@_test("P8-T19: semantic hints passed through to ContentPacket")
def test_semantic_hints_passthrough():
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen",
                   return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
            packet = capture_from_perplexity(
                query=_TEST_QUERY,
                domain_hint="trading-systems",
                project_hint="chaseos",
                topic_hint="btc-etf",
                event_date_hint="2026-03-29",
                desired_output_kind="briefing",
                input_class="source",
                origin_kind="ai-generated",
            )
    _assert(packet.domain_hint == "trading-systems",
            f"domain_hint={packet.domain_hint!r}")
    _assert(packet.project_hint == "chaseos",
            f"project_hint={packet.project_hint!r}")
    _assert(packet.topic_hint == "btc-etf",
            f"topic_hint={packet.topic_hint!r}")
    _assert(packet.event_date_hint == "2026-03-29",
            f"event_date_hint={packet.event_date_hint!r}")
    _assert(packet.desired_output_kind == "briefing",
            f"desired_output_kind={packet.desired_output_kind!r}")
    _assert(packet.input_class == INPUT_CLASS_SOURCE,
            f"input_class={packet.input_class!r}")


@_test("P8-T20: dedup — same content captured twice returns duplicate on second")
def test_dedup_on_repeated_capture():
    from runtime.capture.capture import capture_content
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()

        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
            with patch("urllib.request.urlopen",
                       return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
                packet1 = capture_from_perplexity(query=_TEST_QUERY)
            result1 = capture_content(packet1, vault_root=vault)

            # Same API content → same ContentPacket content → same SHA-256
            with patch("urllib.request.urlopen",
                       return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
                packet2 = capture_from_perplexity(query=_TEST_QUERY)
            result2 = capture_content(packet2, vault_root=vault)

        _assert(not result1.get("is_duplicate"),
                "first capture should not be duplicate")
        _assert(result2.get("is_duplicate"),
                "second capture of identical content should be duplicate")
        _assert("duplicate_of" in result2,
                f"duplicate_of missing; keys={list(result2.keys())}")
        _assert(result2["duplicate_of"] == result1["capture_id"],
                "duplicate_of should reference first capture_id")
        # First file still exists; no new file written
        _assert(Path(result1["content_path"]).exists(),
                "first capture file should still exist")


@_test("P8-T21: CLI capture perplexity --query produces quarantine write")
def test_cli_capture_perplexity():
    from runtime.cli.main import main as cli_main
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()

        argv = [
            "capture", "perplexity",
            "--query", _TEST_QUERY,
            "--domain", "trading-systems",
            "--vault-root", str(vault),
            "--json",
        ]
        output_buf = io.StringIO()
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
            with patch("urllib.request.urlopen",
                       return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
                with patch("sys.stdout", new=output_buf):
                    rc = cli_main(argv)

        output = output_buf.getvalue()

    _assert(rc == 0, f"CLI returned non-zero: {rc}")
    envelope = json.loads(output)
    result = envelope.get("result", envelope)
    _assert(not result.get("is_duplicate"),
            "should not be duplicate on first capture")
    _assert("filename" in result, f"filename missing from CLI JSON output")
    _assert("00_QUARANTINE" in result.get("quarantine_dir", ""),
            f"not in quarantine: {result.get('quarantine_dir')}")


@_test("P8-T22: CLI --json output contains connector-specific fields")
def test_cli_json_output_fields():
    from runtime.cli.main import main as cli_main
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()

        argv = [
            "capture", "perplexity",
            "--query", _TEST_QUERY,
            "--vault-root", str(vault),
            "--json",
        ]
        output_buf = io.StringIO()
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
            with patch("urllib.request.urlopen",
                       return_value=_make_mock_urlopen(_STANDARD_RESPONSE)):
                with patch("sys.stdout", new=output_buf):
                    rc = cli_main(argv)

        envelope = json.loads(output_buf.getvalue())
        result = envelope.get("result", envelope)

    _assert(rc == 0, f"rc={rc}")
    # Standard capture result fields
    _assert("capture_id" in result, f"capture_id missing")
    _assert("content_sha256" in result, f"content_sha256 missing")
    _assert("sidecar_path" in result, f"sidecar_path missing")


@_test("P8-T23: CLI credential error returns exit code 1 with error on stderr")
def test_cli_credential_error():
    from runtime.cli.main import main as cli_main
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()

        argv = [
            "capture", "perplexity",
            "--query", _TEST_QUERY,
            "--vault-root", str(vault),
        ]
        env = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
        stderr_buf = io.StringIO()
        with patch.dict(os.environ, env, clear=True):
            with patch("sys.stderr", new=stderr_buf):
                rc = cli_main(argv)

    _assert(rc == 1, f"should return exit code 1 on credential error; rc={rc}")
    _assert("PERPLEXITY_API_KEY" in stderr_buf.getvalue() or "ERROR" in stderr_buf.getvalue(),
            f"stderr should mention error; got: {stderr_buf.getvalue()!r}")


@_test("P8-T24: backward compat — capture file still works after Pass 8 additions")
def test_backward_compat_capture_file():
    from runtime.cli.main import main as cli_main
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()
        txt_file = vault / "research.txt"
        txt_file.write_text("Some research content here.", encoding="utf-8")

        argv = [
            "capture", "file", str(txt_file),
            "--class", "source",
            "--source", "manual",
            "--title", "Research Note",
            "--vault-root", str(vault),
            "--json",
        ]
        output_buf = io.StringIO()
        with patch("sys.stdout", new=output_buf):
            rc = cli_main(argv)

        envelope = json.loads(output_buf.getvalue())
        result = envelope.get("result", envelope)

    _assert(rc == 0, f"capture file returned rc={rc}")
    _assert(not result.get("is_duplicate"), "should not be duplicate")
    _assert("filename" in result, "filename missing from result")


@_test("P8-T25: model parameter is passed through to API request body")
def test_model_parameter():
    captured_requests = []

    def mock_urlopen_capture(req, timeout=None):
        # Capture the request payload to verify model field
        body = json.loads(req.data.decode("utf-8"))
        captured_requests.append(body)
        return _make_mock_urlopen(_STANDARD_RESPONSE)

    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": _TEST_KEY}):
        with patch("urllib.request.urlopen", side_effect=mock_urlopen_capture):
            capture_from_perplexity(query=_TEST_QUERY, model="sonar-pro")

    _assert(len(captured_requests) == 1, "should have made one API request")
    _assert(captured_requests[0].get("model") == "sonar-pro",
            f"model not passed to API; body={captured_requests[0]}")


# ── Main entry point ───────────────────────────────────────────────────────────

def run_tests() -> tuple[int, int]:
    global _PASS, _FAIL
    _PASS = 0
    _FAIL = 0
    _ERRORS.clear()
    for label, fn in _TESTS:
        print(f"\n[{label}]")
        _run_test(label, fn)
    print(f"\nPass 8: {_PASS} passed, {_FAIL} failed")
    if _ERRORS:
        print("Failures:")
        for e in _ERRORS:
            print(f"  - {e}")
    return _PASS, _FAIL


if __name__ == "__main__":
    p, f = run_tests()
    sys.exit(0 if f == 0 else 1)
