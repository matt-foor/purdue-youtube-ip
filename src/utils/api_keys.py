import json
import os
from typing import Any, Callable, Dict, List, Optional, TypeVar

import streamlit as st


T = TypeVar("T")

PROVIDER_ENV_MAP = {
    "youtube": ("YOUTUBE_API_KEYS", "YOUTUBE_API_KEY"),
    "gemini": ("GEMINI_API_KEYS", "GEMINI_API_KEY"),
    "openai": ("OPENAI_API_KEYS", "OPENAI_API_KEY"),
}


def _coerce_values(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                return _coerce_values(json.loads(text))
            except Exception:
                pass
        values: List[str] = []
        for line in text.splitlines():
            values.extend(part.strip() for part in line.split(","))
        return [item for item in values if item]
    if isinstance(value, (list, tuple, set)):
        out: List[str] = []
        for item in value:
            out.extend(_coerce_values(item))
        return out
    if isinstance(value, dict):
        out: List[str] = []
        for item in value.values():
            out.extend(_coerce_values(item))
        return out
    text = str(value).strip()
    return [text] if text else []


def _secret_values() -> Dict[str, Any]:
    try:
        return dict(st.secrets)
    except Exception:
        return {}


def _indexed_values(prefix: str, mapping: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    base = f"{prefix}_"
    for key in sorted(mapping):
        if not key.startswith(base):
            continue
        suffix = key[len(base) :]
        if suffix.isdigit():
            out.extend(_coerce_values(mapping[key]))
    return out


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def get_provider_keys(provider: str) -> List[str]:
    provider_name = provider.lower().strip()
    if provider_name not in PROVIDER_ENV_MAP:
        raise ValueError(f"Unsupported provider: {provider}")

    plural_name, singular_name = PROVIDER_ENV_MAP[provider_name]
    secret_values = _secret_values()

    keys: List[str] = []
    keys.extend(_coerce_values(secret_values.get(plural_name)))
    keys.extend(_coerce_values(os.getenv(plural_name)))
    keys.extend(_coerce_values(secret_values.get(singular_name)))
    keys.extend(_coerce_values(os.getenv(singular_name)))
    keys.extend(_indexed_values(singular_name, secret_values))
    keys.extend(_indexed_values(singular_name, dict(os.environ)))

    return _dedupe(keys)


def get_provider_key_count(provider: str) -> int:
    return len(get_provider_keys(provider))


def get_primary_provider_key(provider: str) -> Optional[str]:
    keys = get_provider_keys(provider)
    return keys[0] if keys else None


def _cursor_key(provider: str) -> str:
    return f"_provider_key_cursor_{provider.lower().strip()}"


def _get_cursor(provider: str, count: int) -> int:
    if count <= 0:
        return 0
    try:
        return int(st.session_state.get(_cursor_key(provider), 0)) % count
    except Exception:
        return 0


def _set_cursor(provider: str, next_index: int) -> None:
    try:
        st.session_state[_cursor_key(provider)] = next_index
    except Exception:
        pass


def run_with_provider_keys(
    provider: str,
    operation: Callable[[str], T],
    *,
    retryable_error: Optional[Callable[[Exception], bool]] = None,
) -> T:
    keys = get_provider_keys(provider)
    if not keys:
        raise RuntimeError(
            f"No {provider.title()} API keys configured. Add `{provider.upper()}_API_KEYS` "
            f"or `{provider.upper()}_API_KEY` to Streamlit secrets or environment variables."
        )

    start_index = _get_cursor(provider, len(keys))
    last_error: Optional[Exception] = None
    failures: List[str] = []

    for offset in range(len(keys)):
        index = (start_index + offset) % len(keys)
        try:
            result = operation(keys[index])
            _set_cursor(provider, (index + 1) % len(keys))
            return result
        except Exception as exc:
            last_error = exc
            failures.append(f"key {index + 1}: {exc}")
            if retryable_error is not None and not retryable_error(exc):
                raise

    message = f"All configured {provider.title()} API keys failed."
    if failures:
        message = f"{message} {' | '.join(failures[:3])}"
    raise RuntimeError(message) from last_error
