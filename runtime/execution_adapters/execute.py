"""
Runtime execution adapter — LLM synthesis layer.

Routes synthesis requests through the runtime's configured model chain. Workflow
features call this adapter instead of reading provider credentials or embedding
provider-specific endpoints. The adapter resolves provider/runtime configuration,
records provider-state events, and performs the runtime-owned provider call.

Each runtime (openclaw, hermes) declares its primary model + fallback chain in
runtime/{runtime}/model_config.yaml. Updating that file changes the provider or
model without touching workflow code.

Fallback logic:
  - Credential error for one provider/model → try the next configured fallback.
  - Model/network error → try next fallback in chain.
  - All models exhausted → ExecutionAdapterError propagates to caller.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.execution_adapters.model_config import (
    ModelConfigError,
    ModelSpec,
    RuntimeModelConfig,
    load_runtime_model_config,
)
from runtime.providers.state_ledger import (
    ProviderStateEvent,
    ProviderStateLedgerError,
    append_provider_state_event,
    provider_id_from_model_id,
    summarize_provider_state_ledger,
)
from runtime.providers.governance_layer import (
    HIGH_AUTHORITY_TASK_CLASSES,
    classify_provider_strength,
    is_task_allowed_for_strength,
    mark_primary_unhealthy,
    mark_primary_rate_limited,
    normalize_task_class,
    route_task,
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ExecutionAdapterError(Exception):
    """Raised when synthesis fails (all models in chain exhausted)."""


class ExecutionAdapterCredentialError(ExecutionAdapterError):
    """Raised when the selected provider credential is missing."""


# ---------------------------------------------------------------------------
# Runtime → model_config mapping
# ---------------------------------------------------------------------------

ADAPTER_TO_RUNTIME: dict[str, str] = {
    "openclaw": "openclaw",
    "hermes": "hermes",
    "claude": "openclaw",  # legacy/generic label → OpenClaw is the default synthesizer
    "archon": "hermes",   # Archon (Claude Code) proxies through Hermes' model chain
}


def _resolve_runtime(execution_adapter: str) -> str:
    name = (execution_adapter or "").strip().lower()
    resolved = ADAPTER_TO_RUNTIME.get(name)
    if resolved is None:
        raise ExecutionAdapterError(
            f"Unknown execution_adapter '{execution_adapter}'. "
            f"Valid values: {sorted(ADAPTER_TO_RUNTIME)}"
        )
    return resolved


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SynthesisResult:
    text: str
    model_id: str
    runtime: str
    usage: dict[str, Any]
    fallback_used: bool


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def execute_synthesis(
    *,
    prompt_system: str,
    prompt_user: str,
    execution_adapter: str,
    vault_root: str | Path,
    task_class: str = "documentation_draft",
) -> SynthesisResult:
    """
    Synthesize content via the runtime's configured model chain.

    Tries primary model first. On credential/model/network error, moves through
    fallbacks. A missing OpenAI key should not block an Anthropic/local fallback,
    and vice versa; credentials are runtime/provider concerns, not feature logic.
    Raises ExecutionAdapterError if all models fail.
    """
    runtime_name = _resolve_runtime(execution_adapter)

    try:
        config = load_runtime_model_config(runtime_name, vault_root)
    except ModelConfigError as exc:
        raise ExecutionAdapterError(f"Cannot load model config for runtime '{runtime_name}': {exc}") from exc

    last_error: Exception | None = None
    vault_path = Path(vault_root)
    models = list(config.all_models())
    normalized_task_class = normalize_task_class(task_class)
    prior_recovery = summarize_provider_state_ledger(
        vault_path,
        runtime_filter=runtime_name,
    ).get("recovery_to_primary", {})
    prior_fallback_active = prior_recovery.get("status") == "fallback_active"

    for i, model_spec in enumerate(models):
        provider_id = _provider_id_for_model(model_spec)
        _record_provider_state_event(
            vault_path,
            ProviderStateEvent(
                event_type="provider.request",
                runtime=runtime_name,
                provider_id=provider_id,
                model_id=model_spec.model_id,
                source={"surface": "runtime.execution_adapters.execute"},
                data={
                    "attempt_index": i,
                    "role": "primary" if i == 0 else "fallback",
                    "fallback_used": i > 0,
                    "configured_primary_model_id": config.primary.model_id,
                },
            ),
        )
        try:
            api_key = _get_api_key(provider_id)
            raw = _call_provider(
                prompt_system=prompt_system,
                prompt_user=prompt_user,
                model_spec=model_spec,
                provider_id=provider_id,
                api_key=api_key,
            )
            if i == 0 and prior_fallback_active:
                _record_provider_state_event(
                    vault_path,
                    ProviderStateEvent(
                        event_type="provider.recovery_primary_completed",
                        runtime=runtime_name,
                        provider_id=provider_id,
                        model_id=model_spec.model_id,
                        source={"surface": "runtime.execution_adapters.execute"},
                        data={
                            "attempt_index": i,
                            "primary_model_id": model_spec.model_id,
                            "previous_recovery_status": prior_recovery.get("status"),
                        },
                    ),
                )
            return SynthesisResult(
                text=raw["text"],
                model_id=model_spec.model_id,
                runtime=runtime_name,
                usage=raw.get("usage", {}),
                fallback_used=(i > 0),
            )
        except ExecutionAdapterError as exc:
            last_error = exc
            reason = _provider_error_reason(exc)
            if reason == "rate_limit":
                retry_after_seconds = _provider_retry_after_seconds(exc)
                _record_provider_state_event(
                    vault_path,
                    ProviderStateEvent(
                        event_type="provider.rate_limited",
                        runtime=runtime_name,
                        provider_id=provider_id,
                        model_id=model_spec.model_id,
                        source={"surface": "runtime.execution_adapters.execute"},
                        data={
                            "attempt_index": i,
                            "reason": reason,
                            "status_code": _provider_error_status_code(exc),
                            "retry_after_seconds": retry_after_seconds,
                            "error_preview": _error_preview(exc),
                        },
                    ),
                )
                mark_primary_rate_limited(
                    vault_path,
                    provider_id=provider_id,
                    model=model_spec.model_id,
                    runtime=runtime_name,
                    retry_after_seconds=retry_after_seconds,
                    reason=reason,
                    source_command="runtime.execution_adapters.execute",
                )
            elif i == 0:
                mark_primary_unhealthy(
                    vault_path,
                    provider_id=provider_id,
                    model=model_spec.model_id,
                    runtime=runtime_name,
                    reason=reason,
                    source_command="runtime.execution_adapters.execute",
                )
            next_model = models[i + 1] if i + 1 < len(models) else None
            next_provider_id = _provider_id_for_model(next_model) if next_model is not None else None
            next_strength = classify_provider_strength(next_provider_id, next_model.model_id) if next_model is not None else None
            if (
                normalized_task_class in HIGH_AUTHORITY_TASK_CLASSES
                and i == 0
            ):
                decision = route_task(
                    vault_path,
                    task_class=normalized_task_class,
                    original_request=prompt_user,
                    runtime=runtime_name,
                    related_adapter=execution_adapter,
                    primary_provider_id=provider_id,
                    fallback_provider_id=next_provider_id,
                    source_command="runtime.execution_adapters.execute",
                )
                raise ExecutionAdapterError(
                    "RPGL queued high-authority task for primary retry after primary provider failure; "
                    f"queue_item_id={decision.queue_item_id}"
                ) from exc
            if next_model is not None and next_strength is not None and not is_task_allowed_for_strength(
                normalized_task_class,
                next_strength,
            ):
                decision = route_task(
                    vault_path,
                    task_class=normalized_task_class,
                    original_request=prompt_user,
                    runtime=runtime_name,
                    related_adapter=execution_adapter,
                    primary_provider_id=provider_id,
                    fallback_provider_id=next_provider_id,
                    source_command="runtime.execution_adapters.execute",
                )
                raise ExecutionAdapterError(
                    "RPGL denied fallback provider by capability; "
                    f"task_class={normalized_task_class} "
                    f"fallback_provider_id={next_provider_id} "
                    f"fallback_strength={next_strength} "
                    f"queue_item_id={decision.queue_item_id}"
                ) from exc
            if next_model is not None:
                _record_provider_state_event(
                    vault_path,
                    ProviderStateEvent(
                        event_type="provider.fallback_activated",
                        runtime=runtime_name,
                        provider_id=_provider_id_for_model(next_model),
                        model_id=next_model.model_id,
                        source={"surface": "runtime.execution_adapters.execute"},
                        data={
                            "attempt_index": i,
                            "next_attempt_index": i + 1,
                            "reason": reason,
                            "primary_model_id": config.primary.model_id,
                            "failed_model_id": model_spec.model_id,
                            "failed_provider_id": provider_id,
                            "fallback_model_id": next_model.model_id,
                            "fallback_provider_id": _provider_id_for_model(next_model),
                            "error_preview": _error_preview(exc),
                        },
                    ),
                )
            continue  # try next fallback

    raise ExecutionAdapterError(
        f"All {len(models)} model(s) in runtime '{runtime_name}' chain failed. "
        f"Last error: {last_error}"
    )


def _provider_id_for_model(model_spec: ModelSpec) -> str:
    return provider_id_from_model_id(model_spec.model_id) or "unknown"


def _record_provider_state_event(vault_root: Path, event: ProviderStateEvent) -> None:
    try:
        append_provider_state_event(vault_root, event)
    except (OSError, ProviderStateLedgerError) as exc:
        raise ExecutionAdapterError(f"Provider state ledger write failed: {exc}") from exc


def _provider_error_status_code(exc: BaseException) -> int | None:
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, urllib.error.HTTPError):
            return int(current.code)
        current = current.__cause__

    text = str(exc).lower()
    if "http 429" in text or "status 429" in text:
        return 429
    return None


def _provider_retry_after_seconds(exc: BaseException) -> int | None:
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, urllib.error.HTTPError):
            retry_after = current.headers.get("Retry-After") if current.headers else None
            if retry_after is None:
                return None
            try:
                return max(0, int(str(retry_after).strip()))
            except ValueError:
                return None
        current = current.__cause__
    return None


def _provider_error_reason(exc: BaseException) -> str:
    status_code = _provider_error_status_code(exc)
    text = str(exc).lower()
    if status_code == 429 or "rate limit" in text or "rate_limit" in text or "too many requests" in text:
        return "rate_limit"
    if status_code in {500, 502, 503, 504, 529}:
        return "provider_unavailable"
    if "network error" in text or "timed out" in text or "timeout" in text:
        return "network_error"
    return "model_error"


def _error_preview(exc: BaseException) -> str:
    return str(exc).replace("\n", " ")[:300]


# ---------------------------------------------------------------------------
# Provider calls — runtime-owned credential resolution
# ---------------------------------------------------------------------------

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

_PROVIDER_ENV_VARS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def _get_api_key(provider_id: str = "claude") -> str:
    provider = (provider_id or "").strip().lower()
    env_var = _PROVIDER_ENV_VARS.get(provider)
    if not env_var:
        raise ExecutionAdapterCredentialError(
            f"No credential resolver is configured for provider '{provider_id}'."
        )
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise ExecutionAdapterCredentialError(
            f"Missing API key: environment variable '{env_var}' is not set for provider '{provider}'. "
            "Configure the runtime/provider credential before running synthesis workflows."
        )
    return key


def _call_provider(
    *,
    prompt_system: str,
    prompt_user: str,
    model_spec: ModelSpec,
    provider_id: str,
    api_key: str,
) -> dict[str, Any]:
    provider = (provider_id or "").strip().lower()
    if provider in {"claude", "anthropic"}:
        return _call_anthropic(
            prompt_system=prompt_system,
            prompt_user=prompt_user,
            model_spec=model_spec,
            api_key=api_key,
        )
    if provider == "openai":
        return _call_openai_chat_completions(
            prompt_system=prompt_system,
            prompt_user=prompt_user,
            model_spec=model_spec,
            api_key=api_key,
        )
    raise ExecutionAdapterError(
        f"Unsupported provider '{provider_id}' for model '{model_spec.model_id}'. "
        "Update runtime model_config.yaml to a supported runtime provider."
    )


def _call_anthropic(
    *,
    prompt_system: str,
    prompt_user: str,
    model_spec: ModelSpec,
    api_key: str,
) -> dict[str, Any]:
    """
    POST to Anthropic Messages API using stdlib urllib.request.
    Returns dict with 'text' and 'usage' keys.
    Raises ExecutionAdapterError on HTTP/network/JSON failure.
    """
    payload = {
        "model": model_spec.model_id,
        "max_tokens": model_spec.max_tokens,
        "temperature": model_spec.temperature,
        "system": prompt_system,
        "messages": [{"role": "user", "content": prompt_user}],
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": _ANTHROPIC_VERSION,
    }

    req = urllib.request.Request(_ANTHROPIC_API_URL, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw_body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            pass
        raise ExecutionAdapterError(
            f"Anthropic API HTTP {exc.code} for model '{model_spec.model_id}': {error_body[:300]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ExecutionAdapterError(
            f"Network error calling Anthropic API for model '{model_spec.model_id}': {exc.reason}"
        ) from exc

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ExecutionAdapterError(
            f"Invalid JSON response from Anthropic API for model '{model_spec.model_id}': {exc}"
        ) from exc

    # Extract text from content[0]
    content = data.get("content", [])
    if not content or not isinstance(content, list):
        raise ExecutionAdapterError(
            f"Unexpected response structure from Anthropic API for model '{model_spec.model_id}': "
            f"'content' field missing or empty"
        )

    text = content[0].get("text", "")
    if not text:
        raise ExecutionAdapterError(
            f"Empty text in Anthropic API response for model '{model_spec.model_id}'"
        )

    return {"text": text, "usage": data.get("usage", {})}


def _call_openai_chat_completions(
    *,
    prompt_system: str,
    prompt_user: str,
    model_spec: ModelSpec,
    api_key: str,
) -> dict[str, Any]:
    """
    POST to OpenAI-compatible chat completions using stdlib urllib.request.
    Returns dict with 'text' and 'usage' keys.
    Raises ExecutionAdapterError on HTTP/network/JSON failure.
    """
    model_id = _strip_provider_prefix(model_spec.model_id)
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user},
        ],
    }
    token_field = "max_completion_tokens" if _uses_max_completion_tokens(model_id) else "max_tokens"
    payload[token_field] = model_spec.max_tokens
    if not _disallows_temperature(model_id):
        payload["temperature"] = model_spec.temperature

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(
        _OPENAI_CHAT_COMPLETIONS_URL,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw_body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            pass
        raise ExecutionAdapterError(
            f"OpenAI API HTTP {exc.code} for model '{model_id}': {error_body[:300]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ExecutionAdapterError(
            f"Network error calling OpenAI API for model '{model_id}': {exc.reason}"
        ) from exc

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ExecutionAdapterError(
            f"Invalid JSON response from OpenAI API for model '{model_id}': {exc}"
        ) from exc

    choices = data.get("choices", [])
    if not choices or not isinstance(choices, list):
        raise ExecutionAdapterError(
            f"Unexpected response structure from OpenAI API for model '{model_id}': "
            "'choices' field missing or empty"
        )
    message = choices[0].get("message") or {}
    text = message.get("content", "")
    if isinstance(text, list):
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in text
        )
    if not str(text).strip():
        raise ExecutionAdapterError(
            f"Empty text in OpenAI API response for model '{model_id}'"
        )
    return {"text": str(text), "usage": data.get("usage", {})}


def _strip_provider_prefix(model_id: str) -> str:
    text = str(model_id or "").strip()
    if "/" in text:
        prefix, rest = text.split("/", 1)
        if prefix.lower() in {"openai", "anthropic", "claude"}:
            return rest
    return text


def _uses_max_completion_tokens(model_id: str) -> bool:
    text = model_id.lower()
    return text.startswith(("gpt-5", "o1", "o3", "o4"))


def _disallows_temperature(model_id: str) -> bool:
    text = model_id.lower()
    return text.startswith(("gpt-5", "o1", "o3", "o4"))
