"""Explicit source adapters for Capture to Markdown."""

from __future__ import annotations

from dataclasses import replace
import html
import re
from pathlib import Path
import zipfile
from typing import Any
from urllib.parse import urlparse
import zlib

from runtime.browser_runtime.artifacts import validate_browser_artifact_path
from runtime.capture.connectors.browser_connector import (
    MAX_HTML_INPUT_CHARS,
    capture_from_browser,
    load_html_file,
)
from runtime.capture.content_packet import INPUT_CLASS_SOURCE

from .attachments import build_screenshot_attachment
from .models import VisualCapturePacket, build_visual_capture_packet, validate_visual_capture_packet
from .ocr import extract_text_from_image
from .redaction import scan_secret_like_text


CONTROLLED_BROWSER_ARTIFACT_DIRS = (
    "07_LOGS/Browser-Runs",
    "runtime/browser_runtime/artifacts",
    "runtime/studio/webview_artifacts",
)

CONTROLLED_BROWSER_ARTIFACT_SOURCE_SELECTORS = frozenset(
    {
        "browser_runtime_artifact",
        "studio_webview_export",
    }
)

PHOTO_DOCUMENT_TEXT_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".docx",
        ".rtf",
        ".txt",
        ".md",
        ".markdown",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }
)

_IMAGE_TEXT_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_MAX_DOCUMENT_TEXT_CHARS = 500_000

_SOURCE_APP_BY_SELECTOR = {
    "browser_runtime_artifact": "browser-runtime-controlled-artifact",
    "studio_webview_export": "studio-controlled-webview",
}

_FORBIDDEN_ARTIFACT_PATH_MARKERS = (
    "/browser-history/",
    "/chrome-history/",
    "/edge-history/",
    "/cookies/",
    "/sessions/",
    "/sessionstore/",
    "/localstorage/",
    "/indexeddb/",
    "browser-history",
    "chrome-history",
    "edge-history",
    "cookies.sqlite",
    "login data",
    "password-store",
)

_FORBIDDEN_HTML_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("forms_not_allowed", re.compile(r"<\s*form\b", re.IGNORECASE)),
    (
        "password_inputs_not_allowed",
        re.compile(r"<\s*input\b[^>]*\btype\s*=\s*['\"]?password\b", re.IGNORECASE),
    ),
    (
        "file_inputs_not_allowed",
        re.compile(r"<\s*input\b[^>]*\btype\s*=\s*['\"]?file\b", re.IGNORECASE),
    ),
    ("downloads_not_allowed", re.compile(r"<\s*a\b[^>]*\bdownload\b", re.IGNORECASE)),
    (
        "browser_history_not_allowed",
        re.compile(r"\b(?:chrome|edge|about)://history\b|browser[_ -]?history", re.IGNORECASE),
    ),
    (
        "browser_session_storage_not_allowed",
        re.compile(r"\bdocument\.cookie\b|\blocalStorage\b|\bsessionStorage\b", re.IGNORECASE),
    ),
)

_FORBIDDEN_URL_QUERY_KEYS = (
    "access_token=",
    "id_token=",
    "api_key=",
    "apikey=",
    "password=",
    "session=",
    "auth=",
    "bearer=",
)


def capture_from_text(
    *,
    text: str,
    title: str,
    profile: str = "research_note",
    capture_method: str = "manual_paste",
    declared_source: str = "operator_paste",
    **kwargs: Any,
) -> VisualCapturePacket:
    """Build a VCMI packet from operator-provided text without writing."""

    return build_visual_capture_packet(
        title=title,
        raw_extracted_text=text,
        profile=profile,
        capture_method=capture_method,
        declared_source=declared_source,
        **kwargs,
    )


def capture_from_text_file(
    *,
    file_path: str | Path,
    title: str | None = None,
    profile: str = "research_note",
    encoding: str = "utf-8",
    **kwargs: Any,
) -> VisualCapturePacket:
    """Build a VCMI packet from an explicit local text/Markdown file."""

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Capture source file not found: {file_path}")
    text = path.read_text(encoding=encoding)
    resolved_title = title or path.stem.replace("_", " ").replace("-", " ").strip() or "Local File Capture"
    return build_visual_capture_packet(
        title=resolved_title,
        raw_extracted_text=text,
        profile=profile,
        capture_method="local_text_file",
        source_app="local-file",
        source_page_title=path.name,
        source_platform="visual-capture",
        declared_source=str(path.resolve()),
        input_class=INPUT_CLASS_SOURCE,
        **kwargs,
    )


def capture_from_saved_html(
    *,
    file_path: str | Path,
    title: str | None = None,
    source_url: str | None = None,
    profile: str = "research_note",
    **kwargs: Any,
) -> VisualCapturePacket:
    """Build a VCMI packet from a local saved-HTML file via the browser connector."""

    browser_packet = capture_from_browser(
        file_path=file_path,
        title=title,
        source_url=source_url,
        input_class=INPUT_CLASS_SOURCE,
        source_platform="web",
    )
    return build_visual_capture_packet(
        title=browser_packet.title,
        raw_extracted_text=browser_packet.content,
        profile=profile,
        capture_method="saved_html_file",
        source_app="browser-saved-html",
        source_page_title=browser_packet.title,
        source_url=browser_packet.source_url or "",
        source_platform="visual-capture",
        declared_source=browser_packet.original_path_or_uri or str(Path(file_path).resolve()),
        input_class=browser_packet.input_class,
        **kwargs,
    )


def capture_from_controlled_browser_artifact(
    *,
    file_path: str | Path,
    vault_root: str | Path,
    declared_url: str,
    allowed_origin: str | None = None,
    source_selector: str = "browser_runtime_artifact",
    title: str | None = None,
    profile: str = "research_note",
    **kwargs: Any,
) -> VisualCapturePacket:
    """Build a VCMI packet from a confined controlled browser/webview artifact.

    This extractor is intentionally file-based. It does not inspect an active
    browser profile, tab, history database, cookies, local/session storage, or
    credentials. The caller must provide a vault root, a local artifact under an
    allowed browser/webview artifact directory, and the declared source URL.
    """

    selector = str(source_selector or "").strip() or "browser_runtime_artifact"
    if selector not in CONTROLLED_BROWSER_ARTIFACT_SOURCE_SELECTORS:
        raise ValueError(
            "controlled browser source_selector must be one of: "
            f"{', '.join(sorted(CONTROLLED_BROWSER_ARTIFACT_SOURCE_SELECTORS))}"
        )

    declared_origin = _declared_origin(declared_url, field_name="declared_url")
    if allowed_origin:
        allowed = _declared_origin(allowed_origin, field_name="allowed_origin")
        if allowed != declared_origin:
            raise ValueError(
                "declared_url origin does not match allowed_origin "
                f"({declared_origin} != {allowed})"
            )

    validation = validate_browser_artifact_path(
        file_path,
        root=vault_root,
        artifact_type="controlled_html",
        require_exists=True,
        min_bytes=1,
        allowed_dirs=CONTROLLED_BROWSER_ARTIFACT_DIRS,
    )
    if not validation.ok:
        raise ValueError(validation.error or validation.status)
    relative_artifact = validation.relative_path or validation.path
    _validate_controlled_artifact_path(relative_artifact)

    html_content = load_html_file(validation.path)
    _validate_controlled_html(html_content)

    browser_packet = capture_from_browser(
        file_path=validation.path,
        title=title,
        source_url=declared_url,
        input_class=INPUT_CLASS_SOURCE,
        source_platform="web",
    )

    packet_kwargs = dict(kwargs)
    warnings = list(packet_kwargs.pop("extraction_warnings", []) or [])
    warnings.extend(
        [
            "controlled_browser_artifact_confined",
            f"source_selector:{selector}",
            f"declared_origin:{declared_origin}",
        ]
    )
    packet_kwargs.setdefault("confidence", "controlled_source_artifact")

    packet = build_visual_capture_packet(
        title=browser_packet.title,
        raw_extracted_text=browser_packet.content,
        profile=profile,
        capture_method="controlled_browser_dom",
        source_app=_SOURCE_APP_BY_SELECTOR[selector],
        source_page_title=browser_packet.title,
        source_url=declared_url,
        source_platform="visual-capture",
        declared_source=relative_artifact,
        input_class=browser_packet.input_class,
        extraction_warnings=warnings,
        **packet_kwargs,
    )

    chain = list(packet.provenance.get("transformation_chain", []))
    chain.insert(
        1,
        {
            "step": "controlled_browser_artifact_validate",
            "method": "vcmi_controlled_browser_scope_guard",
            "at": packet.captured_at,
            "status": "allowed",
            "source_selector": selector,
            "declared_origin": declared_origin,
            "artifact_path": relative_artifact,
            "allowed_dirs": list(CONTROLLED_BROWSER_ARTIFACT_DIRS),
        },
    )
    controlled_packet = replace(packet, provenance={"transformation_chain": chain})
    validate_visual_capture_packet(controlled_packet, require_no_write=True)
    return controlled_packet


def _declared_origin(url: str, *, field_name: str) -> str:
    raw = str(url or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{field_name} must be a declared http(s) URL with a host.")
    if parsed.username or parsed.password:
        raise ValueError(f"{field_name} must not contain username or password credentials.")
    if any(marker in parsed.query.lower() for marker in _FORBIDDEN_URL_QUERY_KEYS):
        raise ValueError(f"{field_name} query must not contain credential/session markers.")
    if scan_secret_like_text(raw).redaction_count:
        raise ValueError(f"{field_name} contains secret-like material.")
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}"


def _validate_controlled_artifact_path(relative_artifact: str) -> None:
    normalized = "/" + str(relative_artifact).replace("\\", "/").lower().strip("/")
    if any(marker in normalized for marker in _FORBIDDEN_ARTIFACT_PATH_MARKERS):
        raise ValueError(
            "controlled browser artifact path appears to reference browser "
            "history, cookies, sessions, passwords, or storage data."
        )


def _validate_controlled_html(html_content: str) -> None:
    if len(html_content) > MAX_HTML_INPUT_CHARS:
        raise ValueError(
            f"HTML input too large: {len(html_content):,} chars exceeds "
            f"MAX_HTML_INPUT_CHARS={MAX_HTML_INPUT_CHARS:,}"
        )
    for status, pattern in _FORBIDDEN_HTML_PATTERNS:
        if pattern.search(html_content):
            raise ValueError(f"controlled browser artifact blocked: {status}")


def capture_from_screenshot_attachment(
    *,
    file_path: str | Path,
    vault_root: str | Path,
    title: str | None = None,
    source_url: str | None = None,
    profile: str = "research_note",
    **kwargs: Any,
) -> VisualCapturePacket:
    """Build a VCMI packet from an explicit local screenshot attachment.

    This is an attachment-only fallback. It validates and hashes a local image
    file, records the screenshot as evidence, and marks optical character recognition as not performed.
    It does not capture screen pixels, call an optical character recognition engine, call a provider, or
    infer private/authenticated image contents.
    """

    screenshot = build_screenshot_attachment(file_path, vault_root=vault_root)
    resolved_title = (
        title
        or Path(screenshot.attachment.filename).stem.replace("_", " ").replace("-", " ").strip()
        or "Screenshot Attachment"
    )
    packet_kwargs = dict(kwargs)
    warnings = list(packet_kwargs.pop("extraction_warnings", []) or [])
    warnings.extend(screenshot.warnings)
    if packet_kwargs.get("confidence") in {None, "", "operator_supplied"}:
        packet_kwargs["confidence"] = "screenshot_attachment_no_ocr"

    raw_text = (
        "Screenshot attachment imported for operator review. "
        "Optical character recognition text is not available in this pass. "
        f"Attachment: {screenshot.attachment.filename}."
    )
    packet = build_visual_capture_packet(
        title=resolved_title,
        raw_extracted_text=raw_text,
        profile=profile,
        capture_method="screenshot_attachment_import",
        source_app="local-screenshot-file",
        source_page_title=screenshot.attachment.filename,
        source_url=str(source_url or ""),
        source_platform="visual-capture",
        declared_source=screenshot.attachment.relative_path,
        input_class=INPUT_CLASS_SOURCE,
        extraction_status="attachment_only",
        extraction_warnings=warnings,
        attachments=[screenshot.attachment],
        **packet_kwargs,
    )

    chain = list(packet.provenance.get("transformation_chain", []))
    chain.insert(
        1,
        {
            "step": "screenshot_attachment_validate",
            "method": "vcmi_screenshot_attachment_guard",
            "at": packet.captured_at,
            "status": "allowed",
            "attachment_path": screenshot.attachment.relative_path,
            "mime_type": screenshot.attachment.mime_type,
            "size_bytes": screenshot.attachment.size_bytes,
            "sha256": screenshot.attachment.sha256,
            "ocr_status": "not_performed",
            "nonblank_check": "byte-level-only",
        },
    )
    screenshot_packet = replace(packet, provenance={"transformation_chain": chain})
    validate_visual_capture_packet(screenshot_packet, require_no_write=True)
    return screenshot_packet


def capture_from_screenshot_text(
    *,
    file_path: str | Path,
    vault_root: str | Path,
    title: str | None = None,
    source_url: str | None = None,
    profile: str = "research_note",
    local_ocr_command: str | list[str] | tuple[str, ...] | None = None,
    local_ocr_timeout_seconds: int = 20,
    **kwargs: Any,
) -> VisualCapturePacket:
    """Build a VCMI packet from local image text extraction.

    The image must be an explicit vault-local file under the existing screenshot
    evidence allowlist. Text extraction uses only a local command such as
    Tesseract or a configured command; cloud optical character recognition, provider calls, live screen
    capture, active-window capture, and browser profile access remain blocked.
    """

    extraction = extract_text_from_image(
        file_path,
        vault_root=vault_root,
        command=local_ocr_command,
        timeout_seconds=local_ocr_timeout_seconds,
    )
    attachment = extraction.attachment_info.attachment
    resolved_title = (
        title
        or Path(attachment.filename).stem.replace("_", " ").replace("-", " ").strip()
        or "Screenshot Text Extraction"
    )
    packet_kwargs = dict(kwargs)
    warnings = list(packet_kwargs.pop("extraction_warnings", []) or [])
    warnings.extend(extraction.warnings)
    if packet_kwargs.get("confidence") in {None, "", "operator_supplied"}:
        packet_kwargs["confidence"] = "local_optical_character_recognition"

    packet = build_visual_capture_packet(
        title=resolved_title,
        raw_extracted_text=extraction.text,
        profile=profile,
        capture_method="screenshot_local_text_extraction",
        source_app="local-screenshot-file",
        source_page_title=attachment.filename,
        source_url=str(source_url or ""),
        source_platform="visual-capture",
        declared_source=attachment.relative_path,
        input_class=INPUT_CLASS_SOURCE,
        extraction_status="text_extracted",
        extraction_warnings=warnings,
        attachments=[attachment],
        **packet_kwargs,
    )

    chain = list(packet.provenance.get("transformation_chain", []))
    chain.insert(
        1,
        {
            "step": "screenshot_attachment_validate",
            "method": "vcmi_screenshot_attachment_guard",
            "at": packet.captured_at,
            "status": "allowed",
            "attachment_path": attachment.relative_path,
            "mime_type": attachment.mime_type,
            "size_bytes": attachment.size_bytes,
            "sha256": attachment.sha256,
            "ocr_status": "requested",
            "nonblank_check": "byte-level-only",
        },
    )
    chain.insert(
        2,
        {
            "step": "local_optical_character_recognition_extract",
            "method": "local_command_stdout",
            "at": packet.captured_at,
            "status": "text_extracted",
            "engine_id": extraction.engine.engine_id,
            "engine_protocol": extraction.engine.protocol,
            "cloud_optical_character_recognition_allowed": False,
            "provider_call_allowed": False,
            "extracted_text_sha256": extraction.text_sha256,
            "extracted_text_char_count": extraction.text_char_count,
            "secret_scan_required_after_extraction": True,
        },
    )
    ocr_packet = replace(packet, provenance={"transformation_chain": chain})
    validate_visual_capture_packet(ocr_packet, require_no_write=True)
    return ocr_packet


def capture_from_photo_or_document_text(
    *,
    file_path: str | Path,
    vault_root: str | Path,
    title: str | None = None,
    source_url: str | None = None,
    profile: str = "research_note",
    local_ocr_command: str | list[str] | tuple[str, ...] | None = None,
    local_ocr_timeout_seconds: int = 20,
    **kwargs: Any,
) -> VisualCapturePacket:
    """Build a packet from a local photo/image or document text source."""

    path = _resolve_vault_local_document(file_path, vault_root)
    suffix = path.suffix.lower()
    if suffix in _IMAGE_TEXT_EXTENSIONS:
        image_packet = capture_from_screenshot_text(
            file_path=path,
            vault_root=vault_root,
            title=title,
            source_url=source_url,
            profile=profile,
            local_ocr_command=local_ocr_command,
            local_ocr_timeout_seconds=local_ocr_timeout_seconds,
            **kwargs,
        )
        chain = list(image_packet.provenance.get("transformation_chain", []))
        chain.insert(
            1,
            {
                "step": "photo_document_source_route",
                "method": "local_image_text_extraction",
                "at": image_packet.captured_at,
                "status": "image_routed_to_local_text_engine",
                "source_extension": suffix,
            },
        )
        return replace(
            image_packet,
            capture_method="photo_document_image_text_extraction",
            provenance={"transformation_chain": chain},
        )

    extracted = _extract_local_document_text(path)
    resolved_title = (
        title
        or path.stem.replace("_", " ").replace("-", " ").strip()
        or "Photo Document Text Extraction"
    )
    packet_kwargs = dict(kwargs)
    warnings = list(packet_kwargs.pop("extraction_warnings", []) or [])
    warnings.extend(
        [
            "local_document_text_extraction_performed",
            f"document_extension:{suffix}",
            "cloud_optical_character_recognition_blocked",
            "provider_call_blocked",
            "secret_scan_after_extraction_required",
        ]
    )
    if packet_kwargs.get("confidence") in {None, "", "operator_supplied"}:
        packet_kwargs["confidence"] = "local_document_text_extraction"

    packet = build_visual_capture_packet(
        title=resolved_title,
        raw_extracted_text=extracted,
        profile=profile,
        capture_method="photo_document_text_extraction",
        source_app="local-photo-document-file",
        source_page_title=path.name,
        source_url=str(source_url or ""),
        source_platform="visual-capture",
        declared_source=_relative_to_vault(path, vault_root),
        input_class=INPUT_CLASS_SOURCE,
        extraction_status="text_extracted",
        extraction_warnings=warnings,
        **packet_kwargs,
    )
    chain = list(packet.provenance.get("transformation_chain", []))
    chain.insert(
        1,
        {
            "step": "photo_document_text_extract",
            "method": _document_extraction_method(suffix),
            "at": packet.captured_at,
            "status": "text_extracted",
            "source_extension": suffix,
            "source_path": _relative_to_vault(path, vault_root),
            "extracted_text_char_count": len(extracted),
            "cloud_optical_character_recognition_allowed": False,
            "provider_call_allowed": False,
        },
    )
    document_packet = replace(packet, provenance={"transformation_chain": chain})
    validate_visual_capture_packet(document_packet, require_no_write=True)
    return document_packet


def _resolve_vault_local_document(file_path: str | Path, vault_root: str | Path) -> Path:
    vault = Path(vault_root).resolve()
    candidate = Path(file_path)
    resolved = candidate if candidate.is_absolute() else vault / candidate
    resolved = resolved.resolve()
    try:
        relative = resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Photo/document extraction may only read explicit files under the selected vault.") from exc
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"Photo/document source file not found: {file_path}")
    suffix = resolved.suffix.lower()
    if suffix not in PHOTO_DOCUMENT_TEXT_EXTENSIONS:
        raise ValueError(
            "Unsupported photo/document source extension. Supported extensions: "
            f"{', '.join(sorted(PHOTO_DOCUMENT_TEXT_EXTENSIONS))}."
        )
    _validate_document_path_text(relative.as_posix())
    return resolved


def _validate_document_path_text(relative_path: str) -> None:
    normalized = "/" + str(relative_path).replace("\\", "/").lower().strip("/")
    if scan_secret_like_text(normalized).redaction_count:
        raise ValueError("Photo/document source path contains secret-like material.")
    if any(marker in normalized for marker in _FORBIDDEN_ARTIFACT_PATH_MARKERS):
        raise ValueError("Photo/document source path appears to reference browser private data.")


def _extract_local_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        return _normalize_document_text(path.read_text(encoding="utf-8", errors="replace"))
    if suffix == ".docx":
        return _extract_docx_text(path)
    if suffix == ".rtf":
        return _extract_rtf_text(path)
    if suffix == ".pdf":
        return _extract_pdf_embedded_text(path)
    raise ValueError(f"Unsupported photo/document source extension: {suffix}")


def _extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [
                name
                for name in archive.namelist()
                if name == "word/document.xml"
                or (name.startswith("word/") and name.endswith(".xml") and "header" in name)
                or (name.startswith("word/") and name.endswith(".xml") and "footer" in name)
            ]
            chunks = []
            for name in names:
                xml = archive.read(name).decode("utf-8", errors="replace")
                chunks.extend(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, flags=re.DOTALL))
    except zipfile.BadZipFile as exc:
        raise ValueError("Word document could not be opened as a docx file.") from exc
    text = _normalize_document_text("\n".join(html.unescape(_strip_xml_tags(chunk)) for chunk in chunks))
    if not text:
        raise ValueError("Word document contains no extractable text.")
    return text


def _extract_rtf_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\(?:par|line)\b", "\n", raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", raw)
    raw = raw.replace("{", "").replace("}", "")
    text = _normalize_document_text(raw)
    if not text:
        raise ValueError("Rich text document contains no extractable text.")
    return text


def _extract_pdf_embedded_text(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > 25 * 1024 * 1024:
        raise ValueError("PDF is too large for local embedded-text extraction.")
    chunks: list[str] = []
    for stream in _pdf_stream_payloads(data):
        chunks.extend(_extract_pdf_text_operators(stream))
    if not chunks:
        chunks.extend(_extract_pdf_text_operators(data))
    text = _normalize_document_text("\n".join(chunks))
    if not text:
        raise ValueError("PDF contains no extractable embedded text.")
    return text


def _pdf_stream_payloads(data: bytes) -> list[bytes]:
    streams: list[bytes] = []
    for match in re.finditer(rb"(<<.*?>>)\s*stream\r?\n(.*?)\r?\nendstream", data, flags=re.DOTALL):
        header = match.group(1)
        payload = match.group(2)
        if b"/FlateDecode" in header:
            try:
                payload = zlib.decompress(payload)
            except zlib.error:
                continue
        streams.append(payload)
    return streams


def _extract_pdf_text_operators(data: bytes) -> list[str]:
    text = data.decode("latin-1", errors="ignore")
    chunks: list[str] = []
    for match in re.finditer(r"\(((?:\\.|[^\\)])*)\)\s*Tj", text, flags=re.DOTALL):
        chunks.append(_decode_pdf_string(match.group(1)))
    for match in re.finditer(r"\[(.*?)\]\s*TJ", text, flags=re.DOTALL):
        array_body = match.group(1)
        parts = re.findall(r"\((?:\\.|[^\\)])*\)", array_body, flags=re.DOTALL)
        decoded = "".join(_decode_pdf_string(part[1:-1]) for part in parts)
        if decoded:
            chunks.append(decoded)
    return chunks


def _decode_pdf_string(value: str) -> str:
    value = value.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    value = value.replace(r"\n", "\n").replace(r"\r", "\n").replace(r"\t", "\t")
    return value


def _strip_xml_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def _normalize_document_text(value: str) -> str:
    text = str(value or "").replace("\x00", "")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    normalized = "\n".join(line for line in lines if line).strip()
    if len(normalized) > _MAX_DOCUMENT_TEXT_CHARS:
        normalized = normalized[:_MAX_DOCUMENT_TEXT_CHARS].rstrip()
    return normalized


def _relative_to_vault(path: Path, vault_root: str | Path) -> str:
    try:
        return path.resolve().relative_to(Path(vault_root).resolve()).as_posix()
    except ValueError:
        return str(path)


def _document_extraction_method(suffix: str) -> str:
    return {
        ".pdf": "local_pdf_embedded_text_parser",
        ".docx": "local_docx_xml_parser",
        ".rtf": "local_rich_text_parser",
        ".txt": "local_text_file_read",
        ".md": "local_markdown_file_read",
        ".markdown": "local_markdown_file_read",
    }.get(suffix, "local_document_text_parser")
