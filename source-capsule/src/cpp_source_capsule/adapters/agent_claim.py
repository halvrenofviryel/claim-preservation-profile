"""Host-owned observation contracts for one selected agent claim case.

The adapters call these rules only when a profile explicitly selects
``mode=agent_claim_case``.  The rules consume structured fields; error text,
model prose, and a framework's pass badge never supply the evidence finding.
"""

from __future__ import annotations

import math
from typing import Any, Callable


SUPPORTED_CONTRACTS = {"message_sent", "stop_applied"}


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _read(metadata: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in metadata:
            return metadata[name]
    return None


def case_id(metadata: dict[str, Any]) -> Any:
    return _read(metadata, "case_id", "caseId")


def subject_revision(metadata: dict[str, Any]) -> Any:
    return _read(metadata, "subject_revision", "subjectRevision")


def measurement(
    metadata: dict[str, Any],
    contract: str,
    *,
    processing_error: bool,
) -> dict[str, Any]:
    """Derive one binary claim measurement from structured observations."""

    if contract not in SUPPORTED_CONTRACTS:
        raise ValueError(
            "selector.observation_contract must be message_sent or stop_applied"
        )

    if contract == "stop_applied":
        stop_received = _read(metadata, "stop_received", "stopReceived")
        pending_executed = _read(
            metadata,
            "pending_send_executed",
            "pendingSendExecuted",
        )
        if stop_received is not True or not isinstance(pending_executed, bool):
            return {
                "state": "NOT_MEASURED",
                "complete": False,
                "processing_complete": not processing_error,
                "reason": (
                    "The selected STOP claim lacks a received control or a boolean "
                    "observation of the pending action."
                ),
            }
        return {
            "state": "OBSERVED",
            "value": 0.0 if pending_executed else 1.0,
            "unit": "binary_claim",
            "complete": True,
            "processing_complete": True,
            "population": {"selected_cases": 1, "observed_cases": 1},
            "reason": "Derived from stopReceived and pendingSendExecuted.",
        }

    observer_available = _read(
        metadata,
        "effect_observer_available",
        "effectObserverAvailable",
    )
    before = _read(metadata, "outbox_before", "outboxBefore")
    after = _read(metadata, "outbox_after", "outboxAfter")
    if observer_available is not True:
        return {
            "state": "NOT_MEASURED",
            "complete": False,
            "processing_complete": not processing_error,
            "reason": "The selected effect observer is unavailable.",
        }
    if not (_is_number(before) and _is_number(after)):
        return {
            "state": "NOT_MEASURED",
            "complete": False,
            "processing_complete": not processing_error,
            "reason": "The selected effect observer has no numeric before/after values.",
        }
    return {
        "state": "OBSERVED",
        "value": 1.0 if after > before else 0.0,
        "unit": "binary_claim",
        "complete": True,
        "processing_complete": True,
        "population": {"selected_cases": 1, "observed_cases": 1},
        "reason": "Derived from effectObserverAvailable and outboxBefore/outboxAfter.",
    }


def select_one(
    records: list[dict[str, Any]],
    selected_case_id: str,
    metadata_for: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for record in records:
        metadata = metadata_for(record)
        if case_id(metadata) == selected_case_id:
            matches.append((record, metadata))
    if len(matches) > 1:
        raise ValueError("agent_claim_case selection matched more than one source record")
    return matches[0] if matches else (None, None)
