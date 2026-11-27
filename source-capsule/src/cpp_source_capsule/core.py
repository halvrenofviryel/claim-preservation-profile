"""Deterministic claim-capsule construction and verification."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from typing import Any

EVIDENCE_FINDINGS = {"SUPPORTED", "REFUTED", "NOT_MEASURED", "INCONCLUSIVE"}
APPLICABILITY_STATES = {"CURRENT", "STALE", "UNKNOWN"}
PROCESSING_STATES = {"COMPLETED", "ERROR"}
MAPPING_COVERAGE_STATES = {"DECLARED_SELECTED_FIELDS"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _is_sha256_id(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        return False
    return all(character in "0123456789abcdef" for character in value[7:])


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def validate_profile(profile: dict[str, Any]) -> None:
    _require_mapping(profile, "profile")
    for name in ("profile_version", "recorded_at", "claim", "subject", "evaluation_contract"):
        if name not in profile:
            raise ValueError(f"profile.{name} is required")
    for group, fields in {
        "claim": ("id", "text"),
        "subject": ("id", "revision"),
        "evaluation_contract": ("id", "revision", "criterion"),
    }.items():
        obj = _require_mapping(profile[group], f"profile.{group}")
        for field in fields:
            if field not in obj:
                raise ValueError(f"profile.{group}.{field} is required")
    criterion = _require_mapping(
        profile["evaluation_contract"]["criterion"],
        "profile.evaluation_contract.criterion",
    )
    if criterion.get("operator") not in {"gte", "gt", "lte", "lt", "eq"}:
        raise ValueError("criterion.operator must be gte, gt, lte, lt, or eq")
    if not _is_number(criterion.get("threshold")):
        raise ValueError("criterion.threshold must be numeric")


def _compare(value: float, operator: str, threshold: float) -> bool:
    return {
        "gte": value >= threshold,
        "gt": value > threshold,
        "lte": value <= threshold,
        "lt": value < threshold,
        "eq": value == threshold,
    }[operator]


def _source_revision(source_binding: dict[str, Any]) -> tuple[bool, str | None]:
    revision = _require_mapping(
        source_binding.get("subject_revision"),
        "source_binding.subject_revision",
    )
    observed = revision.get("observed")
    value = revision.get("value")
    if not isinstance(observed, bool):
        raise ValueError("source_binding.subject_revision.observed must be boolean")
    if observed and not isinstance(value, str):
        raise ValueError("an observed source subject revision must have a string value")
    if not observed and value is not None:
        raise ValueError("an unobserved source subject revision must have a null value")
    source_path = revision.get("source_path")
    if observed and not isinstance(source_path, str):
        raise ValueError("an observed source subject revision must have a string source_path")
    if not observed and source_path is not None:
        raise ValueError("an unobserved source subject revision must have a null source_path")
    return observed, value


def _validate_mapping_loss(mapping_loss: dict[str, Any]) -> None:
    mapping_loss = _require_mapping(mapping_loss, "mapping_loss")
    if mapping_loss.get("coverage") not in MAPPING_COVERAGE_STATES:
        raise ValueError("mapping_loss.coverage is not recognized")
    for name in ("declared", "admitted", "omitted", "unavailable"):
        entries = mapping_loss.get(name)
        if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
            raise ValueError(f"mapping_loss.{name} must be an array of objects")
    for index, entry in enumerate(mapping_loss["declared"]):
        for name in ("declared_path", "target_path"):
            if not isinstance(entry.get(name), str) or not entry[name]:
                raise ValueError(f"mapping_loss.declared[{index}].{name} must be a string")
    for index, entry in enumerate(mapping_loss["admitted"]):
        paths = entry.get("source_paths")
        if not isinstance(paths, list) or not paths or not all(isinstance(path, str) and path for path in paths):
            raise ValueError(f"mapping_loss.admitted[{index}].source_paths must contain strings")
        for name in ("target_path", "transform"):
            if not isinstance(entry.get(name), str) or not entry[name]:
                raise ValueError(f"mapping_loss.admitted[{index}].{name} must be a string")
    for group, path_name in (("omitted", "source_path"), ("unavailable", "target_path")):
        for index, entry in enumerate(mapping_loss[group]):
            for name in (path_name, "reason"):
                if not isinstance(entry.get(name), str) or not entry[name]:
                    raise ValueError(f"mapping_loss.{group}[{index}].{name} must be a string")


def _derive_evidence_and_processing(
    measurement: dict[str, Any],
    criterion: dict[str, Any],
) -> tuple[str, str, str, str]:
    state = measurement.get("state")
    processing_complete = measurement.get("processing_complete")
    if not isinstance(processing_complete, bool):
        return (
            "NOT_MEASURED",
            "ERROR",
            "The measurement does not declare whether source processing completed.",
            "The admitted measurement lacks a boolean processing_complete field.",
        )
    if state == "ERROR":
        return (
            "NOT_MEASURED",
            "ERROR",
            "The source reports an execution or processing error; no evidence finding is derived.",
            "The admitted source state is ERROR.",
        )
    if state == "NOT_MEASURED":
        return (
            "NOT_MEASURED",
            "COMPLETED" if processing_complete else "ERROR",
            "The selected measurement is absent or was not completed.",
            (
                "The adapter completed and admitted no selected measurement."
                if processing_complete
                else "The source processing did not complete and no selected measurement was admitted."
            ),
        )
    if state != "OBSERVED":
        return (
            "NOT_MEASURED",
            "ERROR",
            "The measurement state is unrecognized; no evidence finding is derived.",
            "The admitted measurement state is not recognized by this capsule version.",
        )
    if measurement.get("complete") is not True:
        return (
            "INCONCLUSIVE",
            "COMPLETED" if processing_complete else "ERROR",
            "The source contains a partial or incompletely scored population.",
            (
                "The adapter completed and admitted an incomplete observed population."
                if processing_complete
                else "The adapter admitted a partial observed population with a source processing error."
            ),
        )

    value = measurement.get("value")
    if not _is_number(value):
        return (
            "NOT_MEASURED",
            "ERROR",
            "The observed measurement has no numeric value; no evidence finding is derived.",
            "The complete OBSERVED measurement is malformed because value is not numeric.",
        )
    passed = _compare(value, criterion["operator"], criterion["threshold"])
    if passed:
        return (
            "SUPPORTED",
            "COMPLETED",
            "The complete observed value satisfies the declared criterion.",
            "The adapter completed and admitted a complete numeric measurement.",
        )
    return (
        "REFUTED",
        "COMPLETED",
        "The complete observed value does not satisfy the declared criterion.",
        "The adapter completed and admitted a complete numeric measurement.",
    )


def _recorded_applicability(
    source_binding: dict[str, Any],
    recorded_subject_revision: str,
) -> tuple[str, str]:
    observed, source_revision = _source_revision(source_binding)
    if not observed:
        return "UNKNOWN", "The source does not expose a subject revision for this adapter."
    if source_revision != recorded_subject_revision:
        return "STALE", "The admitted source revision differs from the recorded subject revision."
    return "CURRENT", "The admitted source revision matches the recorded subject revision."


def derive_assessment(
    measurement: dict[str, Any],
    criterion: dict[str, Any],
    *,
    source_binding: dict[str, Any],
    recorded_subject_revision: str,
) -> dict[str, Any]:
    """Derive separate evidence, applicability, and processing axes."""

    evidence, processing, evidence_basis, processing_basis = _derive_evidence_and_processing(
        measurement,
        criterion,
    )
    applicability, applicability_basis = _recorded_applicability(
        source_binding,
        recorded_subject_revision,
    )
    return {
        "evidence_finding": evidence,
        "applicability": applicability,
        "processing": processing,
        "basis": {
            "evidence_finding": evidence_basis,
            "applicability": applicability_basis,
            "processing": processing_basis,
        },
        "qualifications": [
            "These axes are derived from admitted source fields and the declared criterion.",
            "They do not establish semantic truth, evaluation validity, safety, independence, or production fitness.",
        ],
    }


def current_applicability(
    *,
    recorded_subject_revision: str,
    source_binding: dict[str, Any],
    current_subject_revision: str | None,
) -> tuple[str, str]:
    if current_subject_revision is None:
        return "UNKNOWN", "No current subject revision was supplied to the verifier."
    if current_subject_revision != recorded_subject_revision:
        return "STALE", "The supplied current subject revision differs from the recorded revision."
    observed, source_revision = _source_revision(source_binding)
    if not observed:
        return "UNKNOWN", "The source did not expose a revision that can bind this measurement to the subject."
    if source_revision != recorded_subject_revision:
        return "STALE", "The admitted source revision differs from the recorded subject revision."
    return "CURRENT", "The supplied current revision and admitted source revision match the recorded revision."


def validate_capsule_structure(capsule: dict[str, Any]) -> None:
    _require_mapping(capsule, "capsule")
    required = (
        "capsule_id",
        "capsule_version",
        "created_at",
        "claim",
        "subject",
        "evaluation_contract",
        "source",
        "source_binding",
        "mapping_loss",
        "selection",
        "measurement",
        "assessment",
        "scope",
    )
    for name in required:
        if name not in capsule:
            raise ValueError(f"capsule.{name} is required")
    if capsule["capsule_version"] != "0.3":
        raise ValueError("capsule.capsule_version must be 0.3")
    if not _is_sha256_id(capsule["capsule_id"]):
        raise ValueError("capsule.capsule_id must be a sha256 identifier")
    validate_profile(
        {
            "profile_version": capsule["capsule_version"],
            "recorded_at": capsule["created_at"],
            "claim": capsule["claim"],
            "subject": capsule["subject"],
            "evaluation_contract": capsule["evaluation_contract"],
        }
    )
    _source_revision(_require_mapping(capsule["source_binding"], "capsule.source_binding"))
    _validate_mapping_loss(capsule["mapping_loss"])
    source = _require_mapping(capsule["source"], "capsule.source")
    for name in ("format", "ref", "sha256", "adapter_version"):
        if name not in source:
            raise ValueError(f"capsule.source.{name} is required")
    if source["format"] not in {"inspect-ai-v2", "promptfoo-jsonl"}:
        raise ValueError("capsule.source.format is not recognized")
    if not isinstance(source["ref"], str) or not source["ref"]:
        raise ValueError("capsule.source.ref must be a non-empty string")
    if not _is_sha256_id(source["sha256"]):
        raise ValueError("capsule.source.sha256 must be a sha256 identifier")
    if not isinstance(source["adapter_version"], str) or not source["adapter_version"]:
        raise ValueError("capsule.source.adapter_version must be a non-empty string")
    _require_mapping(capsule["selection"], "capsule.selection")
    _require_mapping(capsule["scope"], "capsule.scope")
    measurement = _require_mapping(capsule["measurement"], "capsule.measurement")
    if measurement.get("state") not in {"OBSERVED", "NOT_MEASURED", "ERROR"}:
        raise ValueError("capsule.measurement.state is not recognized")
    if not isinstance(measurement.get("complete"), bool):
        raise ValueError("capsule.measurement.complete must be boolean")
    if not isinstance(measurement.get("processing_complete"), bool):
        raise ValueError("capsule.measurement.processing_complete must be boolean")
    if measurement["complete"] and (
        measurement.get("state") != "OBSERVED" or not measurement["processing_complete"]
    ):
        raise ValueError("a complete measurement must be OBSERVED with completed processing")
    if measurement.get("state") in {"NOT_MEASURED", "ERROR"} and measurement["complete"]:
        raise ValueError("NOT_MEASURED and ERROR states cannot be complete")
    if measurement.get("state") == "ERROR" and measurement["processing_complete"]:
        raise ValueError("an ERROR measurement cannot declare completed processing")
    assessment = _require_mapping(capsule["assessment"], "capsule.assessment")
    if assessment.get("evidence_finding") not in EVIDENCE_FINDINGS:
        raise ValueError("capsule.assessment.evidence_finding is not recognized")
    if assessment.get("applicability") not in APPLICABILITY_STATES:
        raise ValueError("capsule.assessment.applicability is not recognized")
    if assessment.get("processing") not in PROCESSING_STATES:
        raise ValueError("capsule.assessment.processing is not recognized")
    basis = _require_mapping(assessment.get("basis"), "capsule.assessment.basis")
    for axis in ("evidence_finding", "applicability", "processing"):
        if not isinstance(basis.get(axis), str):
            raise ValueError(f"capsule.assessment.basis.{axis} must be a string")
    qualifications = assessment.get("qualifications")
    if not isinstance(qualifications, list) or not all(isinstance(item, str) for item in qualifications):
        raise ValueError("capsule.assessment.qualifications must be an array of strings")


def build_capsule(
    profile: dict[str, Any],
    *,
    source_format: str,
    source_ref: str,
    source_bytes: bytes,
    adapter_version: str,
    selection: dict[str, Any],
    measurement: dict[str, Any],
    source_binding: dict[str, Any],
    mapping_loss: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic capsule from a declared profile and admitted measurement."""

    validate_profile(profile)
    recorded_revision = str(profile["subject"]["revision"])
    observed, source_revision = _source_revision(source_binding)
    if observed and source_revision != recorded_revision:
        raise ValueError(
            "the source subject revision does not match profile.subject.revision; "
            "build a profile for the observed source revision"
        )
    criterion = deepcopy(profile["evaluation_contract"]["criterion"])
    assessment = derive_assessment(
        measurement,
        criterion,
        source_binding=source_binding,
        recorded_subject_revision=recorded_revision,
    )
    body = {
        "capsule_version": "0.3",
        "created_at": profile["recorded_at"],
        "claim": deepcopy(profile["claim"]),
        "subject": deepcopy(profile["subject"]),
        "evaluation_contract": deepcopy(profile["evaluation_contract"]),
        "source": {
            "format": source_format,
            "ref": source_ref,
            "sha256": sha256_bytes(source_bytes),
            "adapter_version": adapter_version,
        },
        "source_binding": deepcopy(source_binding),
        "mapping_loss": deepcopy(mapping_loss),
        "selection": deepcopy(selection),
        "measurement": deepcopy(measurement),
        "assessment": assessment,
        "scope": deepcopy(profile.get("scope", {})),
    }
    capsule = {"capsule_id": sha256_bytes(canonical_bytes(body)), **body}
    validate_capsule_structure(capsule)
    return capsule


def verify_capsule(
    capsule: dict[str, Any],
    *,
    source_bytes: bytes | None = None,
    current_subject_revision: str | None = None,
) -> dict[str, Any]:
    """Verify capsule integrity and, when supplied, rederive fields from source bytes."""

    checks: dict[str, bool] = {}
    problems: list[str] = []
    verification_level = "SOURCE_DERIVED" if source_bytes is not None else "CAPSULE_ONLY"

    try:
        validate_capsule_structure(capsule)
        checks["structure"] = True
    except (KeyError, TypeError, ValueError) as exc:
        checks["structure"] = False
        problems.append(f"structure: {exc}")

    try:
        body = {key: deepcopy(value) for key, value in capsule.items() if key != "capsule_id"}
        expected_id = sha256_bytes(canonical_bytes(body))
        checks["capsule_digest"] = capsule.get("capsule_id") == expected_id
    except (AttributeError, TypeError, ValueError) as exc:
        checks["capsule_digest"] = False
        problems.append(f"capsule digest: {exc}")
    if not checks["capsule_digest"] and not any(p.startswith("capsule digest:") for p in problems):
        problems.append("capsule_id does not match the canonical capsule body")

    current_axis = "UNKNOWN"
    current_basis = "Verification could not derive current applicability."
    try:
        criterion = capsule["evaluation_contract"]["criterion"]
        recorded_revision = str(capsule["subject"]["revision"])
        stored_assessment = derive_assessment(
            capsule["measurement"],
            criterion,
            source_binding=capsule["source_binding"],
            recorded_subject_revision=recorded_revision,
        )
        checks["stored_assessment"] = canonical_bytes(capsule["assessment"]) == canonical_bytes(stored_assessment)
        if not checks["stored_assessment"]:
            problems.append("assessment does not match the admitted measurement, source binding, and criterion")
        current_axis, current_basis = current_applicability(
            recorded_subject_revision=recorded_revision,
            source_binding=capsule["source_binding"],
            current_subject_revision=current_subject_revision,
        )
    except (KeyError, TypeError, ValueError) as exc:
        checks["stored_assessment"] = False
        problems.append(f"assessment derivation: {exc}")

    source_check = "NOT_CHECKED"
    if source_bytes is not None:
        source_check = "CHECKED"
        source = capsule.get("source", {}) if isinstance(capsule, dict) else {}
        checks["source_digest"] = source.get("sha256") == sha256_bytes(source_bytes)
        if not checks["source_digest"]:
            problems.append("source bytes do not match source.sha256")

        try:
            from .adapters import get_adapter

            adapter = get_adapter(source.get("format"), source.get("adapter_version"))
            checks["adapter_supported"] = True
        except (TypeError, ValueError) as exc:
            checks["adapter_supported"] = False
            checks["source_admission"] = False
            checks["source_selection"] = False
            checks["source_measurement"] = False
            checks["source_binding"] = False
            checks["source_mapping_loss"] = False
            problems.append(f"source adapter: {exc}")
        else:
            try:
                re_selection, re_measurement, re_binding, re_mapping_loss = adapter.admit(
                    source_bytes,
                    capsule.get("selection", {}),
                )
                checks["source_admission"] = True
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                checks["source_admission"] = False
                checks["source_selection"] = False
                checks["source_measurement"] = False
                checks["source_binding"] = False
                checks["source_mapping_loss"] = False
                problems.append(f"source admission: {exc}")
            else:
                checks["source_selection"] = canonical_bytes(re_selection) == canonical_bytes(capsule.get("selection"))
                checks["source_measurement"] = canonical_bytes(re_measurement) == canonical_bytes(capsule.get("measurement"))
                checks["source_binding"] = canonical_bytes(re_binding) == canonical_bytes(capsule.get("source_binding"))
                checks["source_mapping_loss"] = canonical_bytes(re_mapping_loss) == canonical_bytes(
                    capsule.get("mapping_loss")
                )
                if not checks["source_selection"]:
                    problems.append("selection cannot be rederived from the source with the recorded adapter")
                if not checks["source_measurement"]:
                    problems.append("measurement cannot be rederived from the source with the recorded adapter")
                if not checks["source_binding"]:
                    problems.append("subject binding cannot be rederived from the source with the recorded adapter")
                if not checks["source_mapping_loss"]:
                    problems.append("mapping loss cannot be rederived from the source with the recorded adapter")

    return {
        "valid": all(checks.values()),
        "verification_level": verification_level,
        "checks": checks,
        "source_bytes": source_check,
        "recorded_assessment": capsule.get("assessment") if isinstance(capsule, dict) else None,
        "current_applicability": current_axis,
        "current_applicability_basis": current_basis,
        "problems": problems,
        "limitation": (
            "SOURCE_DERIVED rechecks the implemented adapter mapping; CAPSULE_ONLY does not. "
            "Neither level establishes semantic truth, evaluation validity, source independence, or safety."
        ),
    }
