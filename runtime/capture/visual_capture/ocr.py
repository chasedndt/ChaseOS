"""Local optical character recognition adapter for Capture to Markdown."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from collections.abc import Sequence
from typing import Any

from .attachments import ScreenshotAttachmentInfo, build_screenshot_attachment
from .local_image_text_engine import ENGINE_ID as BUILTIN_LOCAL_IMAGE_TEXT_ENGINE_ID
from .local_image_text_engine import extract_text_from_pixel_image
from .local_image_text_engine import local_image_text_engine_command


LOCAL_OCR_POLICY_ID = "capture_to_markdown.local_optical_character_recognition.v1"
LOCAL_OCR_ENV_COMMAND = "CHASEOS_LOCAL_OCR_COMMAND"
DEFAULT_OCR_TIMEOUT_SECONDS = 20
WINDOWS_MEDIA_OCR_ENGINE_ID = "windows-media-ocr"
_BLOCKED_SHELL_COMMANDS = {
    "cmd",
    "cmd.exe",
    "powershell",
    "powershell.exe",
    "pwsh",
    "pwsh.exe",
    "wscript",
    "wscript.exe",
    "cscript",
    "cscript.exe",
}


class LocalOpticalCharacterRecognitionError(ValueError):
    """Raised when local optical character recognition cannot complete."""


@dataclass(frozen=True)
class LocalOcrEngine:
    available: bool
    engine_id: str
    protocol: str
    command: tuple[str, ...]
    status: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "engine_id": self.engine_id,
            "protocol": self.protocol,
            "command": list(self.command),
            "status": self.status,
            "reason": self.reason,
            "cloud_optical_character_recognition_allowed": False,
            "provider_call_allowed": False,
        }


@dataclass(frozen=True)
class LocalOcrResult:
    text: str
    text_sha256: str
    text_char_count: int
    engine: LocalOcrEngine
    attachment_info: ScreenshotAttachmentInfo
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "text_extracted",
            "text_sha256": self.text_sha256,
            "text_char_count": self.text_char_count,
            "engine": self.engine.to_dict(),
            "attachment": self.attachment_info.attachment.to_dict(),
            "warnings": list(self.warnings),
            "policy": local_ocr_policy(),
        }


def local_ocr_policy() -> dict[str, Any]:
    return {
        "policy_id": LOCAL_OCR_POLICY_ID,
        "status": "local_only",
        "requires_explicit_vault_local_image": True,
        "validates_attachment_before_text_extraction": True,
        "cloud_optical_character_recognition_allowed": False,
        "provider_call_allowed": False,
        "ambient_screen_capture_allowed": False,
        "active_window_capture_allowed": False,
        "browser_profile_access_allowed": False,
        "secret_scan_required_after_extraction": True,
        "writes_on_preview": False,
    }


def build_local_ocr_status_model(
    *,
    command: str | Sequence[str] | None = None,
) -> dict[str, Any]:
    engine = resolve_local_ocr_engine(command)
    return {
        "ok": True,
        "surface": "capture_to_markdown_local_optical_character_recognition",
        "policy": local_ocr_policy(),
        "engine": engine.to_dict(),
        "readiness": {
            "local_optical_character_recognition_adapter_ready": True,
            "local_engine_available": engine.available,
            "cloud_optical_character_recognition_blocked": True,
            "provider_call_blocked": True,
            "explicit_image_required": True,
            "screen_capture_blocked": True,
            "secret_scan_after_extraction_required": True,
        },
    }


def resolve_local_ocr_engine(command: str | Sequence[str] | None = None) -> LocalOcrEngine:
    prefix = _coerce_command_prefix(command)
    if prefix:
        return _engine_from_prefix(prefix)

    env_prefix = _coerce_command_prefix(os.environ.get(LOCAL_OCR_ENV_COMMAND))
    if env_prefix:
        return _engine_from_prefix(env_prefix)

    tesseract = shutil.which("tesseract")
    if tesseract:
        return LocalOcrEngine(
            available=True,
            engine_id="tesseract",
            protocol="tesseract_stdout",
            command=(tesseract,),
            status="available",
        )

    if _windows_ocr_engine_available():
        return LocalOcrEngine(
            available=True,
            engine_id=WINDOWS_MEDIA_OCR_ENGINE_ID,
            protocol="windows_media_ocr",
            command=(),
            status="available",
            reason="Windows local optical character recognition is available.",
        )

    builtin_command = tuple(local_image_text_engine_command())
    builtin_script = Path(builtin_command[-1]) if builtin_command else Path("")
    if builtin_script.is_file():
        return LocalOcrEngine(
            available=True,
            engine_id=BUILTIN_LOCAL_IMAGE_TEXT_ENGINE_ID,
            protocol="stdout_image_path",
            command=builtin_command,
            status="available",
            reason="Repo-owned local image text engine is available.",
        )

    return LocalOcrEngine(
        available=False,
        engine_id="none",
        protocol="not_configured",
        command=(),
        status="unavailable",
        reason="No local image text engine was found.",
    )


def extract_text_from_image(
    file_path: str | Path,
    *,
    vault_root: str | Path,
    command: str | Sequence[str] | None = None,
    timeout_seconds: int = DEFAULT_OCR_TIMEOUT_SECONDS,
) -> LocalOcrResult:
    """Extract text from an explicit vault-local image through a local command."""

    attachment_info = build_screenshot_attachment(
        file_path,
        vault_root=vault_root,
        optical_character_recognition_requested=True,
    )
    engine = resolve_local_ocr_engine(command)
    if not engine.available:
        raise LocalOpticalCharacterRecognitionError(engine.reason or engine.status)

    image_path = Path(attachment_info.absolute_path)
    if engine.engine_id == BUILTIN_LOCAL_IMAGE_TEXT_ENGINE_ID:
        output = _normalize_extracted_text(extract_text_from_pixel_image(image_path))
    elif engine.engine_id == WINDOWS_MEDIA_OCR_ENGINE_ID or engine.protocol == "windows_media_ocr":
        output = _normalize_extracted_text(_extract_text_with_windows_ocr(image_path))
    else:
        completed = _run_local_ocr_command(engine, image_path, timeout_seconds=timeout_seconds)
        output = _normalize_extracted_text(completed.stdout)
    if not output:
        raise LocalOpticalCharacterRecognitionError(
            "Local optical character recognition returned no text."
        )

    warnings = [
        warning
        for warning in attachment_info.warnings
        if warning not in {"ocr_not_performed", "local_only_ocr_deferred"}
    ]
    warnings.extend(
        [
            "local_optical_character_recognition_performed",
            f"local_optical_character_recognition_engine:{engine.engine_id}",
            "cloud_optical_character_recognition_blocked",
            "secret_scan_after_extraction_required",
        ]
    )
    digest = hashlib.sha256(output.encode("utf-8")).hexdigest()
    return LocalOcrResult(
        text=output,
        text_sha256=digest,
        text_char_count=len(output),
        engine=engine,
        attachment_info=attachment_info,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _coerce_command_prefix(command: str | Sequence[str] | None) -> tuple[str, ...]:
    if command is None:
        return ()
    if isinstance(command, str):
        raw = command.strip()
        if not raw:
            return ()
        if raw.startswith("["):
            try:
                decoded = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LocalOpticalCharacterRecognitionError(
                    "Local optical character recognition command JSON is invalid."
                ) from exc
            return _coerce_command_prefix(decoded)
        if Path(raw).exists():
            return (raw,)
        return tuple(part for part in shlex.split(raw, posix=False) if part)
    return tuple(str(part) for part in command if str(part).strip())


def _engine_from_prefix(prefix: Sequence[str]) -> LocalOcrEngine:
    if not prefix:
        return resolve_local_ocr_engine(None)
    exe = prefix[0]
    executable_name = Path(exe).name.lower()
    if executable_name in {"windows-ocr", "windows-media-ocr", "winrt-ocr"}:
        if _windows_ocr_engine_available():
            return LocalOcrEngine(
                available=True,
                engine_id=WINDOWS_MEDIA_OCR_ENGINE_ID,
                protocol="windows_media_ocr",
                command=tuple(prefix),
                status="available",
                reason="Windows local optical character recognition is available.",
            )
        return LocalOcrEngine(
            available=False,
            engine_id=WINDOWS_MEDIA_OCR_ENGINE_ID,
            protocol="windows_media_ocr",
            command=tuple(prefix),
            status="unavailable",
            reason="Windows local optical character recognition packages or engine are unavailable.",
        )
    if executable_name in _BLOCKED_SHELL_COMMANDS:
        return LocalOcrEngine(
            available=False,
            engine_id="blocked-shell-launcher",
            protocol="blocked",
            command=tuple(prefix),
            status="blocked_by_policy",
            reason=(
                "Shell launchers are blocked for local optical character "
                "recognition commands."
            ),
        )
    resolved = shutil.which(exe) if not Path(exe).exists() else str(Path(exe))
    if not resolved:
        return LocalOcrEngine(
            available=False,
            engine_id="configured-command",
            protocol="stdout_image_path",
            command=tuple(prefix),
            status="unavailable",
            reason=f"Configured local optical character recognition command not found: {exe}",
        )
    command = (resolved, *tuple(prefix[1:]))
    executable_name = Path(resolved).name.lower()
    if executable_name in _BLOCKED_SHELL_COMMANDS:
        return LocalOcrEngine(
            available=False,
            engine_id="blocked-shell-launcher",
            protocol="blocked",
            command=command,
            status="blocked_by_policy",
            reason=(
                "Shell launchers are blocked for local optical character "
                "recognition commands."
            ),
        )
    is_tesseract = "tesseract" in executable_name
    return LocalOcrEngine(
        available=True,
        engine_id="tesseract" if is_tesseract else "configured-command",
        protocol="tesseract_stdout" if is_tesseract else "stdout_image_path",
        command=command,
        status="available",
    )


def _run_local_ocr_command(
    engine: LocalOcrEngine,
    image_path: Path,
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    if engine.protocol == "tesseract_stdout":
        argv = [*engine.command, str(image_path), "stdout", "--psm", "6"]
    elif engine.protocol == "stdout_image_path":
        argv = [*engine.command, str(image_path)]
    else:
        raise LocalOpticalCharacterRecognitionError(
            f"Unsupported local optical character recognition protocol: {engine.protocol}"
        )

    kwargs: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "timeout": max(1, int(timeout_seconds or DEFAULT_OCR_TIMEOUT_SECONDS)),
        "shell": False,
    }
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        completed = subprocess.run(argv, **kwargs)
    except subprocess.TimeoutExpired as exc:
        raise LocalOpticalCharacterRecognitionError(
            "Local optical character recognition timed out."
        ) from exc
    except OSError as exc:
        raise LocalOpticalCharacterRecognitionError(
            f"Local optical character recognition command failed to start: {exc}"
        ) from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise LocalOpticalCharacterRecognitionError(
            "Local optical character recognition command failed"
            + (f": {stderr}" if stderr else ".")
        )
    return completed


def _windows_ocr_engine_available() -> bool:
    try:
        from winrt.windows.media.ocr import OcrEngine

        return OcrEngine.try_create_from_user_profile_languages() is not None
    except Exception:
        return False


def _extract_text_with_windows_ocr(image_path: Path) -> str:
    import asyncio

    async def _run() -> str:
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.storage import FileAccessMode, StorageFile

        engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            raise LocalOpticalCharacterRecognitionError(
                "Windows local optical character recognition engine is unavailable."
            )
        file = await StorageFile.get_file_from_path_async(str(image_path.resolve()))
        stream = await file.open_async(FileAccessMode.READ)
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        return getattr(result, "text", "") or ""

    try:
        return asyncio.run(_run())
    except LocalOpticalCharacterRecognitionError:
        raise
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
    except Exception as exc:
        raise LocalOpticalCharacterRecognitionError(
            f"Windows local optical character recognition failed: {exc}"
        ) from exc


def _normalize_extracted_text(value: str) -> str:
    lines = [line.rstrip() for line in str(value or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    text = "\n".join(lines).strip()
    return "\n".join(line for line in text.split("\n") if line.strip())
