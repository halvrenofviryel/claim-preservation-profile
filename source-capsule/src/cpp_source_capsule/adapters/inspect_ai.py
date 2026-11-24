"""Narrow importer for selected Inspect AI eval-log v2 result fields."""

from __future__ import annotations

import json
import math
from typing import Any

from . import agent_claim

ADAPTER_VERSION = "0.1.0a4"


def _inspect_agent_metadata(sample: dict[str, Any]) -> dict[str, Any]:
    metadata = sample.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _agent_claim_mapping_loss(
    data: dict[str, Any],
    selected: dict[str, Any] | None,
    selector: dict[str, Any],
) -> dict[str, Any]:
    contract = selector.get("observation_contract")
    observed_paths = ["samples[*].metadata.case_id", "eval.model"]
    if contract == "stop_applied":
        observed_paths.extend(
            [
                "samples[*].metadata.stop_received",
                "samples[*].metadata.pending_send_executed",
            ]
        )
    elif contract == "message_sent":
        observed_paths.extend(
            [
                "samples[*].metadata.effect_observer_available",
                "samples[*].metadata.outbox_before",
                "samples[*].metadata.outbox_after",
            ]
        )
    unavailable = []
    admitted = []
    if selected is None:
        unavailable.append(
            {
                "target_path": "measurement.value",
                "reason": "SELECTED_AGENT_CASE_IS_ABSENT",
            }
        )
    else:
        admitted.append(
            {
                "source_paths": observed_paths,
                "target_path": "measurement",
                "transform": f"STRUCTURED_{str(contract).upper()}_CONTRACT",
            }
        )
    eval_record = data.get("eval")
    if isinstance(eval_record, dict) and isinstance(eval_record.get("model"), str):
        admitted.append(
            {
                "source_paths": ["eval.model"],
                "target_path": "source_binding.subject_revision",
                "transform": "DIRECT_STRING",
            }
        )
    else:
        unavailable.append(
            {
                "target_path": "source_binding.subject_revision",
                "reason": "INSPECT_EVAL_MODEL_IS_NOT_AVAILABLE_AS_A_STRING",
            }
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
                "source_path": "Inspect fields except the selected structured case and eval.model",
                "reason": "SOURCE_FIELD_OUTSIDE_SELECTED_AGENT_CLAIM",
            }
        ],
        "unavailable": unavailable,
    }


def _admit_agent_claim(
    data: dict[str, Any],
    selector: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    selected_case_id = selector.get("case_id")
    contract = selector.get("observation_contract")
    unit = selector.get("unit", "binary_claim")
    if not isinstance(selected_case_id, str) or not selected_case_id:
        raise ValueError("Inspect selector.case_id must be a non-empty string.")
    if contract not in agent_claim.SUPPORTED_CONTRACTS:
        raise ValueError(
            "Inspect selector.observation_contract must be message_sent or stop_applied."
        )
    if unit != "binary_claim":
        raise ValueError("Inspect agent_claim_case selector.unit must be binary_claim.")
    samples = data.get("samples")
    sample_records = [sample for sample in samples if isinstance(sample, dict)] if isinstance(samples, list) else []
    selected, metadata = agent_claim.select_one(
        sample_records,
        selected_case_id,
        _inspect_agent_metadata,
    )
    source_model = data.get("eval", {}).get("model") if isinstance(data.get("eval"), dict) else None
    source_binding = {
        "subject_revision": {
            "observed": isinstance(source_model, str),
            "value": source_model if isinstance(source_model, str) else None,
            "source_path": "eval.model" if isinstance(source_model, str) else None,
        }
    }
    selection = {
        "mode": "agent_claim_case",
        "case_id": selected_case_id,
        "observation_contract": contract,
        "unit": unit,
    }
    mapping_loss = _agent_claim_mapping_loss(data, selected, selector)
    status = data.get("status")
    if status == "error":
        return selection, {
            "state": "ERROR",
            "complete": False,
            "processing_complete": False,
            "reason": "Inspect log status is error.",
        }, source_binding, mapping_loss
    if selected is None or metadata is None:
        return selection, {
            "state": "NOT_MEASURED",
            "complete": False,
            "processing_complete": status == "success",
            "reason": "The selected agent claim case is absent from the source.",
        }, source_binding, mapping_loss
    return (
        selection,
        agent_claim.measurement(metadata, contract, processing_error=False),
        source_binding,
        mapping_loss,
    )


def _mapping_loss(data: dict[str, Any], selector: dict[str, Any]) -> dict[str, Any]:
    top_level = set(data)
    admitted_roots = {"status", "eval", "results"}
    admitted: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    if "status" in data:
        admitted.append(
            {
                "source_paths": ["status"],
                "target_path": "measurement.state",
                "transform": "STATUS_CLASSIFICATION",
            }
        )
        admitted.append(
            {
                "source_paths": ["status"],
                "target_path": "measurement.processing_complete",
                "transform": "SUCCESS_STATUS_CHECK",
            }
        )
    else:
        unavailable.append(
            {
                "target_path": "measurement.state",
                "reason": "INSPECT_STATUS_IS_ABSENT",
            }
        )
        unavailable.append(
            {
                "target_path": "measurement.processing_complete",
                "reason": "INSPECT_STATUS_IS_ABSENT",
            }
        )

    eval_record = data.get("eval")
    if isinstance(eval_record, dict) and isinstance(eval_record.get("model"), str):
        admitted.append(
            {
                "source_paths": ["eval.model"],
                "target_path": "source_binding.subject_revision",
                "transform": "DIRECT_STRING",
            }
        )
    else:
        unavailable.append(
            {
                "target_path": "source_binding.subject_revision",
                "reason": "INSPECT_EVAL_MODEL_IS_NOT_AVAILABLE_AS_A_STRING",
            }
        )

    results = data.get("results")
    selected_score = None
    if isinstance(results, dict):
        selected_score = next(
            (
                score
                for score in results.get("scores", [])
                if isinstance(score, dict) and score.get("name") == selector.get("score_name")
            ),
            None,
        )
    if isinstance(results, dict) and isinstance(selected_score, dict):
        admitted.append(
            {
                "source_paths": [
                    "results.total_samples",
                    "results.completed_samples",
                    f"results.scores[name={selector.get('score_name')!r}].scored_samples",
                    f"results.scores[name={selector.get('score_name')!r}].unscored_samples",
                ],
                "target_path": "measurement.population",
                "transform": "DIRECT_SELECTED_SCORE",
            }
        )
        metric = selected_score.get("metrics", {}).get(selector.get("metric_name"))
        if isinstance(metric, dict) and _is_number(metric.get("value")):
            admitted.append(
                {
                    "source_paths": [
                        f"results.scores[name={selector.get('score_name')!r}].metrics[{selector.get('metric_name')!r}].value"
                    ],
                    "target_path": "measurement.value",
                    "transform": "DIRECT_SELECTED_METRIC",
                }
            )
        else:
            unavailable.append(
                {
                    "target_path": "measurement.value",
                    "reason": "SELECTED_INSPECT_METRIC_IS_ABSENT_OR_NONNUMERIC",
                }
            )
    else:
        unavailable.extend(
            [
                {
                    "target_path": "measurement.population",
                    "reason": "SELECTED_INSPECT_SCORE_POPULATION_IS_UNAVAILABLE",
                },
                {
                    "target_path": "measurement.value",
                    "reason": "SELECTED_INSPECT_METRIC_IS_UNAVAILABLE",
                },
            ]
        )

    omitted = [
        {
            "source_path": key,
            "reason": "TOP_LEVEL_FIELD_OUTSIDE_ADAPTER_SCOPE",
        }
        for key in sorted(top_level - admitted_roots)
    ]
    if isinstance(eval_record, dict) and set(eval_record) - {"model"}:
        omitted.append(
            {
                "source_path": "eval.* except eval.model",
                "reason": "EVALUATION_METADATA_OUTSIDE_SELECTED_CLAIM",
            }
        )
    if isinstance(results, dict):
        omitted.append(
            {
                "source_path": "results.* except selected score population and metric",
                "reason": "UNSELECTED_RESULTS_OUTSIDE_ADAPTER_SCOPE",
            }
        )
    return {
        "coverage": "DECLARED_SELECTED_FIELDS",
        "declared": [
            {
                "declared_path": f"profile.selector.{name}",
                "target_path": f"selection.{name}",
            }
            for name in ("score_name", "metric_name", "unit")
        ]
        + [
            {
                "declared_path": "profile.selector.unit",
                "target_path": "measurement.unit",
            }
        ],
        "admitted": admitted,
        "omitted": omitted,
        "unavailable": unavailable,
    }


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def admit(
    source_bytes: bytes,
    selector: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    data = json.loads(source_bytes)
    if selector.get("mode") == "agent_claim_case":
        return _admit_agent_claim(data, selector)
    status = data.get("status")
    selection = {
        "score_name": selector.get("score_name"),
        "metric_name": selector.get("metric_name"),
        "unit": selector.get("unit", "ratio"),
    }
    for name in ("score_name", "metric_name", "unit"):
        if not isinstance(selection[name], str) or not selection[name]:
            raise ValueError(f"Inspect selector.{name} must be a non-empty string.")
    source_model = data.get("eval", {}).get("model") if isinstance(data.get("eval"), dict) else None
    source_binding = {
        "subject_revision": {
            "observed": isinstance(source_model, str),
            "value": source_model if isinstance(source_model, str) else None,
            "source_path": "eval.model" if isinstance(source_model, str) else None,
        }
    }
    mapping_loss = _mapping_loss(data, selector)
    if status == "error":
        return selection, {
            "state": "ERROR",
            "complete": False,
            "processing_complete": False,
            "reason": "Inspect log status is error.",
        }, source_binding, mapping_loss
    if status != "success" or not isinstance(data.get("results"), dict):
        return (
            selection,
            {
                "state": "NOT_MEASURED",
                "complete": False,
                "processing_complete": False,
                "reason": "Inspect results are absent or the run did not finish successfully.",
            },
            source_binding,
            mapping_loss,
        )

    results = data["results"]
    match = next(
        (score for score in results.get("scores", []) if score.get("name") == selector.get("score_name")),
        None,
    )
    metric = None if match is None else match.get("metrics", {}).get(selector.get("metric_name"))
    if not isinstance(metric, dict) or not _is_number(metric.get("value")):
        return (
            selection,
            {
                "state": "NOT_MEASURED",
                "complete": False,
                "processing_complete": True,
                "reason": "The selected Inspect score metric is absent.",
            },
            source_binding,
            mapping_loss,
        )

    total = results.get("total_samples")
    completed = results.get("completed_samples")
    scored = match.get("scored_samples")
    unscored = match.get("unscored_samples", 0)
    complete = (
        _is_int(total)
        and _is_int(completed)
        and _is_int(scored)
        and _is_int(unscored)
        and total == completed
        and total == scored + unscored
        and scored == total
        and unscored == 0
    )
    return (
        selection,
        {
            "state": "OBSERVED",
            "value": metric["value"],
            "unit": selection["unit"],
            "complete": complete,
            "processing_complete": True,
            "population": {
                "total_samples": total,
                "completed_samples": completed,
                "scored_samples": scored,
                "unscored_samples": unscored,
            },
        },
        source_binding,
        mapping_loss,
    )
