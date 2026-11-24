"""Narrow importer for selected Promptfoo JSONL output fields."""

from __future__ import annotations

import json
import math
from typing import Any

from . import agent_claim

ADAPTER_VERSION = "0.1.0a4"


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_graded(row: dict[str, Any]) -> bool:
    grading = row.get("gradingResult")
    return (
        isinstance(grading, dict)
        and isinstance(grading.get("pass"), bool)
        and _is_number(row.get("score"))
    )


def _mapping_loss(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_fields = set().union(*(set(row) for row in rows)) if rows else set()
    admitted_fields = {"gradingResult", "score", "error"}
    measured = [
        row for row in rows if _is_graded(row)
    ]
    admitted: list[dict[str, Any]] = []
    unavailable = [
        {
            "target_path": "source_binding.subject_revision",
            "reason": "PROMPTFOO_JSONL_DOES_NOT_EXPOSE_A_SUBJECT_REVISION",
        }
    ]
    if rows:
        admitted.append(
            {
                "source_paths": ["rows", "rows[*].gradingResult", "rows[*].score", "rows[*].error"],
                "target_path": "measurement.population",
                "transform": "ROW_CLASSIFICATION",
            }
        )
        admitted.append(
            {
                "source_paths": ["rows[*].gradingResult", "rows[*].score", "rows[*].error"],
                "target_path": "measurement.processing_complete",
                "transform": "UNMEASURED_ERROR_CLASSIFICATION",
            }
        )
    else:
        admitted.append(
            {
                "source_paths": ["rows"],
                "target_path": "measurement.processing_complete",
                "transform": "EMPTY_FILE_ADMISSION_COMPLETED",
            }
        )
        unavailable.append(
            {
                "target_path": "measurement.population",
                "reason": "PROMPTFOO_JSONL_HAS_NO_ROWS",
            }
        )
    if measured:
        admitted.append(
            {
                "source_paths": ["rows[*].score"],
                "target_path": "measurement.value",
                "transform": "ARITHMETIC_MEAN_OF_NUMERIC_GRADED_ROWS",
            }
        )
    else:
        unavailable.append(
            {
                "target_path": "measurement.value",
                "reason": "PROMPTFOO_JSONL_HAS_NO_NUMERIC_GRADED_ROWS",
            }
        )
    return {
        "coverage": "DECLARED_SELECTED_FIELDS",
        "declared": [
            {
                "declared_path": f"profile.selector.{name}",
                "target_path": f"selection.{name}",
            }
            for name in ("aggregate", "unit")
        ]
        + [
            {
                "declared_path": "profile.selector.unit",
                "target_path": "measurement.unit",
            }
        ],
        "admitted": admitted,
        "omitted": [
            {
                "source_path": f"rows[*].{field}",
                "reason": "ROW_FIELD_OUTSIDE_ADAPTER_SCOPE",
            }
            for field in sorted(row_fields - admitted_fields)
        ],
        "unavailable": unavailable,
    }


def _agent_metadata(row: dict[str, Any]) -> dict[str, Any]:
    response = row.get("response")
    if not isinstance(response, dict):
        return {}
    metadata = response.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _agent_claim_mapping_loss(
    rows: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    selector: dict[str, Any],
) -> dict[str, Any]:
    observed_paths = [
        "rows[*].response.metadata.caseId",
        "rows[*].response.metadata.subjectRevision",
    ]
    contract = selector.get("observation_contract")
    if contract == "stop_applied":
        observed_paths.extend(
            [
                "rows[*].response.metadata.stopReceived",
                "rows[*].response.metadata.pendingSendExecuted",
            ]
        )
    elif contract == "message_sent":
        observed_paths.extend(
            [
                "rows[*].response.metadata.effectObserverAvailable",
                "rows[*].response.metadata.outboxBefore",
                "rows[*].response.metadata.outboxAfter",
            ]
        )
    admitted = []
    unavailable = []
    if selected is None:
        unavailable.extend(
            [
                {
                    "target_path": "measurement.value",
                    "reason": "SELECTED_AGENT_CASE_IS_ABSENT",
                },
                {
                    "target_path": "source_binding.subject_revision",
                    "reason": "SELECTED_AGENT_CASE_IS_ABSENT",
                },
            ]
        )
    else:
        admitted.extend(
            [
                {
                    "source_paths": observed_paths,
                    "target_path": "measurement",
                    "transform": f"STRUCTURED_{str(contract).upper()}_CONTRACT",
                },
                {
                    "source_paths": ["rows[*].response.metadata.subjectRevision"],
                    "target_path": "source_binding.subject_revision",
                    "transform": "DIRECT_STRING",
                },
                {
                    "source_paths": ["rows[*].error"],
                    "target_path": "measurement.processing_complete",
                    "transform": "ERROR_PRESENCE_ONLY",
                },
            ]
        )
    return {
        "coverage": "DECLARED_SELECTED_FIELDS",
        "declared": [
            {
                "declared_path": f"profile.selector.{name}",
                "target_path": f"selection.{name}",
            }
            for name in ("mode", "case_id", "observation_contract", "unit")
        ],
        "admitted": admitted,
        "omitted": [
            {
                "source_path": "rows[*].* except the selected structured case fields",
                "reason": "SOURCE_FIELD_OUTSIDE_SELECTED_AGENT_CLAIM",
            }
        ],
        "unavailable": unavailable,
    }


def _admit_agent_claim(
    rows: list[dict[str, Any]],
    selector: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    selected_case_id = selector.get("case_id")
    contract = selector.get("observation_contract")
    unit = selector.get("unit", "binary_claim")
    if not isinstance(selected_case_id, str) or not selected_case_id:
        raise ValueError("Promptfoo selector.case_id must be a non-empty string.")
    if contract not in agent_claim.SUPPORTED_CONTRACTS:
        raise ValueError(
            "Promptfoo selector.observation_contract must be message_sent or stop_applied."
        )
    if unit != "binary_claim":
        raise ValueError("Promptfoo agent_claim_case selector.unit must be binary_claim.")
    selected, metadata = agent_claim.select_one(rows, selected_case_id, _agent_metadata)
    revision = agent_claim.subject_revision(metadata or {})
    source_binding = {
        "subject_revision": {
            "observed": isinstance(revision, str),
            "value": revision if isinstance(revision, str) else None,
            "source_path": (
                "rows[*].response.metadata.subjectRevision"
                if isinstance(revision, str)
                else None
            ),
        }
    }
    selection = {
        "mode": "agent_claim_case",
        "case_id": selected_case_id,
        "observation_contract": contract,
        "unit": unit,
    }
    mapping_loss = _agent_claim_mapping_loss(rows, selected, selector)
    if selected is None or metadata is None:
        return selection, {
            "state": "NOT_MEASURED",
            "complete": False,
            "processing_complete": True,
            "reason": "The selected agent claim case is absent from the source.",
        }, source_binding, mapping_loss
    return (
        selection,
        agent_claim.measurement(
            metadata,
            contract,
            processing_error=bool(selected.get("error")),
        ),
        source_binding,
        mapping_loss,
    )


def admit(
    source_bytes: bytes,
    selector: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = [json.loads(line) for line in source_bytes.decode("utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Each Promptfoo JSONL row must be an object.")
    if selector.get("mode") == "agent_claim_case":
        return _admit_agent_claim(rows, selector)
    selection = {
        "aggregate": selector.get("aggregate", "mean_score"),
        "unit": selector.get("unit", "ratio"),
    }
    if selection["aggregate"] != "mean_score":
        raise ValueError("The Promptfoo adapter supports only aggregate='mean_score'.")
    if not isinstance(selection["unit"], str) or not selection["unit"]:
        raise ValueError("Promptfoo selector.unit must be a non-empty string.")
    source_binding = {
        "subject_revision": {
            "observed": False,
            "value": None,
            "source_path": None,
        }
    }
    mapping_loss = _mapping_loss(rows)
    if not rows:
        return selection, {
            "state": "NOT_MEASURED",
            "complete": False,
            "processing_complete": True,
            "reason": "The JSONL file has no rows.",
        }, source_binding, mapping_loss

    measured = [
        row for row in rows if _is_graded(row)
    ]
    processing_errors = [
        row
        for row in rows
        if row.get("error")
        and not _is_graded(row)
    ]
    if processing_errors and not measured:
        return selection, {
            "state": "ERROR",
            "complete": False,
            "processing_complete": False,
            "reason": "Promptfoo rows report errors and no admitted graded result exists.",
        }, source_binding, mapping_loss
    if not measured:
        return selection, {
            "state": "NOT_MEASURED",
            "complete": False,
            "processing_complete": True,
            "reason": "No row contains gradingResult.pass as a boolean and a finite numeric score.",
        }, source_binding, mapping_loss

    value = sum(float(row["score"]) for row in measured) / len(measured)
    passed = [row for row in measured if row.get("gradingResult", {}).get("pass") is True]
    failed = [row for row in measured if row.get("gradingResult", {}).get("pass") is False]
    measured_error_text = [row for row in measured if row.get("error")]
    return selection, {
        "state": "OBSERVED",
        "value": value,
        "unit": selection["unit"],
        "complete": len(measured) == len(rows) and not processing_errors,
        "processing_complete": not processing_errors,
        "population": {
            "total_rows": len(rows),
            "measured_rows": len(measured),
            "unmeasured_rows": len(rows) - len(measured),
            "passed_rows": len(passed),
            "failed_rows": len(failed),
            "other_result_rows": len(measured) - len(passed) - len(failed),
            "measured_error_text_rows": len(measured_error_text),
            "processing_error_rows": len(processing_errors),
        },
    }, source_binding, mapping_loss
