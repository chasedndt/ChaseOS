"""Secret-like text detection and redaction for capture previews."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


SECRET_REDACTION_TOKEN = "[REDACTED_SECRET]"

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "openai_style_api_key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE),
    ),
    (
        "github_style_token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE),
    ),
    (
        "gitlab_style_token",
        re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b", re.IGNORECASE),
    ),
    (
        "slack_style_token",
        re.compile(r"\bxox(?:b|p|a|r|s)-[A-Za-z0-9-]{20,}\b", re.IGNORECASE),
    ),
    (
        "password_assignment",
        re.compile(r"(?i)(\b(?:password|passwd|pwd)\s*[:=]\s*)(?!\[REDACTED_SECRET\])([^\s,;]{8,})"),
    ),
    (
        "token_assignment",
        re.compile(r"(?i)(\b(?:api[_ -]?key|secret|token|credential)\s*[:=]\s*)(?!\[REDACTED_SECRET\])([^\s,;]{8,})"),
    ),
    (
        "bearer_token",
        re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{16,})"),
    ),
)


@dataclass(frozen=True)
class SecretRedactionReport:
    """Result of scanning one text field for secret-like strings."""

    contains_secret: bool
    redacted_text: str
    redaction_count: int
    indicator_categories: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scan_secret_like_text(text: str | None) -> SecretRedactionReport:
    """Scan and redact secret-like text without returning the raw secret."""

    redacted = str(text or "")
    categories: list[str] = []
    redaction_count = 0

    for category, pattern in SECRET_PATTERNS:
        matched = False

        def repl(match: re.Match[str]) -> str:
            nonlocal matched, redaction_count
            matched = True
            redaction_count += 1
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}{SECRET_REDACTION_TOKEN}"
            return SECRET_REDACTION_TOKEN

        redacted = pattern.sub(repl, redacted)
        if matched:
            categories.append(category)

    return SecretRedactionReport(
        contains_secret=bool(redaction_count),
        redacted_text=redacted,
        redaction_count=redaction_count,
        indicator_categories=tuple(dict.fromkeys(categories)),
    )


def redact_secret_like_text(text: str | None) -> str:
    """Return text with secret-like strings replaced by a stable token."""

    return scan_secret_like_text(text).redacted_text
