"""Narrow source adapters for the CPP Source Capsule prototype."""

from __future__ import annotations

from typing import Any

from . import inspect_ai, promptfoo

_ADAPTERS = {
    "inspect-ai-v2": inspect_ai,
    "promptfoo-jsonl": promptfoo,
}


def get_adapter(source_format: str, adapter_version: str):
    """Return an exact supported adapter or reject the version/format pair."""

    adapter = _ADAPTERS.get(source_format)
    if adapter is None:
        raise ValueError(f"unsupported source format: {source_format!r}")
    if adapter_version != adapter.ADAPTER_VERSION:
        raise ValueError(
            f"unsupported adapter version {adapter_version!r} for {source_format}; "
            f"supported version is {adapter.ADAPTER_VERSION!r}"
        )
    return adapter


def admit_source(
    source_format: str,
    source_bytes: bytes,
    selector: dict[str, Any],
    *,
    adapter_version: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run the exact supported adapter version for a recorded source format."""

    adapter = get_adapter(source_format, adapter_version)
    return adapter.admit(source_bytes, selector)
