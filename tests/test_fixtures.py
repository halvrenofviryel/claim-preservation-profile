"""Tests over the conformance corpus."""

from __future__ import annotations

import hashlib
import json
import re

import pytest

PASSING_RELATIONS = {"EQUIVALENT", "NARROWER", "SUPPORTED_STRENGTHENING"}
NON_SUCCESS_RELATIONS = {"NOT_MEASURED", "INCONCLUSIVE", "ERROR"}
LEGAL_RELATIONS = PASSING_RELATIONS | NON_SUCCESS_RELATIONS | {"AMPLIFIED_UNSUPPORTED", "INCOMPARABLE"}

SEED_NEGATIVE_IDS = [f"CPP-N{n:02d}" for n in range(1, 21)]


def _violations(fixture: dict) -> list[str]:
    return sorted(set(fixture.get("violates", []) + fixture.get("expected_violations", [])))


# --- corpus shape ---------------------------------------------------------


def test_all_twenty_supplied_negative_fixtures_are_present(negative_fixtures):
    assert [f["id"] for f in negative_fixtures] == SEED_NEGATIVE_IDS
    assert len(negative_fixtures) == 20


#: SHA-256 of `negative_fixtures_v0.1.json` as supplied in the v0.1 seed bundle.
SEED_NEGATIVE_CORPUS_SHA256 = "c32ee2c01f53d57aaeb0d7fb1415ec992220a08e798f2ddde8e93f0a4906da85"


def test_negative_corpus_is_byte_identical_to_the_seed_bundle(repo_root):
    """The seed negative corpus was copied, not rewritten. This pins its exact bytes
    against the digest of the supplied bundle, so an edit cannot pass silently — the
    seed file itself lives outside the repository and cannot be compared directly."""
    raw = (repo_root / "conformance" / "negative-fixtures.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SEED_NEGATIVE_CORPUS_SHA256


def test_negative_fixture_names_and_order_are_pinned(negative_fixtures):
    names = [f["name"] for f in negative_fixtures]
    assert names == [
        "population_scope_broadening",
        "temporal_scope_broadening",
        "certainty_upgrade",
        "causal_upgrade",
        "drop_material_qualifier",
        "drop_nonclaim",
        "not_measured_to_pass",
        "inconclusive_to_pass",
        "error_removed_from_denominator",
        "withheld_cases_dropped",
        "unresolvable_reference_upgraded",
        "signature_to_truth",
        "ack_to_effect",
        "self_report_to_independent_observation",
        "semantic_state_collapse",
        "mutable_basis_as_frozen",
        "redaction_removes_limitation",
        "instrumentation_changes_timeout",
        "evaluation_awareness_generalized_to_deployment",
        "silent_evidence_sink_failure",
    ]


def test_at_least_eight_positive_fixtures(positive_fixtures):
    assert len(positive_fixtures) >= 8


def test_ids_are_unique_across_both_corpora(negative_fixtures, positive_fixtures):
    ids = [f["id"] for f in negative_fixtures + positive_fixtures]
    assert len(ids) == len(set(ids))


def test_ids_follow_the_corpus_convention(negative_fixtures, positive_fixtures):
    assert all(re.fullmatch(r"CPP-N\d{2}", f["id"]) for f in negative_fixtures)
    assert all(re.fullmatch(r"CPP-P\d{2}", f["id"]) for f in positive_fixtures)


def test_expected_relations_are_legal(negative_fixtures, positive_fixtures):
    for fixture in negative_fixtures + positive_fixtures:
        assert fixture["expected_relation"] in LEGAL_RELATIONS


def test_negative_fixtures_never_declare_a_passing_relation(negative_fixtures):
    for fixture in negative_fixtures:
        assert fixture["expected_relation"] not in PASSING_RELATIONS


def test_positive_fixtures_declare_a_passing_relation_and_no_violations(positive_fixtures):
    for fixture in positive_fixtures:
        assert fixture["expected_relation"] in PASSING_RELATIONS
        assert not _violations(fixture)


def test_declared_violations_name_real_cpp_requirements(report, negative_fixtures):
    defined = set(report["corpus_validation"]["requirements_defined"])
    assert len(defined) == 20
    for fixture in negative_fixtures:
        declared = _violations(fixture)
        assert declared, f"{fixture['id']} declares no violated requirement"
        assert set(declared) <= defined, f"{fixture['id']} names undefined requirements"


def test_declared_strengthening_always_carries_added_evidence(positive_fixtures):
    for fixture in positive_fixtures:
        if fixture["expected_relation"] == "SUPPORTED_STRENGTHENING":
            assert fixture.get("added_evidence"), f"{fixture['id']} strengthens with no added evidence"


# --- schema validation ----------------------------------------------------


def test_corpus_validates_against_the_common_schema(report):
    corpus = report["corpus_validation"]
    assert corpus["schema_validation_state"] == "MEASURED"
    assert corpus["problems"] == []
    assert corpus["valid"] is True


def test_supplied_negative_fixtures_still_validate_against_the_original_seed_schema(
    repo_root, negative_fixtures
):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (repo_root / "conformance" / "negative-fixture.schema.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    for fixture in negative_fixtures:
        assert list(validator.iter_errors(fixture)) == []


def test_positive_fixtures_validate_against_the_common_schema(repo_root, positive_fixtures):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((repo_root / "conformance" / "fixture.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for fixture in positive_fixtures:
        assert list(validator.iter_errors(fixture)) == [], fixture["id"]


def test_result_schema_is_valid_and_keeps_dimensions_separate(repo_root):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (repo_root / "spec" / "v0.1" / "claim-preservation-result.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    required = set(schema["required"])
    assert {
        "cpp_version",
        "case_id",
        "relation",
        "input_claim_ref",
        "output_claim_ref",
        "dimensions",
        "added_evidence",
        "violations",
        "observer_effect",
        "qualifications",
        "non_claims",
        "evidence_refs",
        "basis",
    } <= required
    dimension = schema["$defs"]["dimension_result"]
    assert set(dimension["required"]) == {"status", "measurement_state"}
    for field in ("supporting_evidence", "qualification", "measurement_state", "status"):
        assert field in dimension["properties"]
    assert schema["properties"]["dimensions"]["type"] == "object"
    assert "minProperties" in schema["properties"]["dimensions"]


def test_result_schema_rejects_a_passing_relation_alongside_violations(repo_root):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (repo_root / "spec" / "v0.1" / "claim-preservation-result.schema.json").read_text(encoding="utf-8")
    )
    result = {
        "cpp_version": "0.1",
        "case_id": "synthetic",
        "relation": "EQUIVALENT",
        "input_claim_ref": "claim://in",
        "output_claim_ref": "claim://out",
        "dimensions": {
            "population_scope": {"status": "AMPLIFIED_UNSUPPORTED", "measurement_state": "MEASURED"}
        },
        "added_evidence": [],
        "violations": [{"requirement": "CPP-2", "detail": "scope broadened"}],
        "observer_effect": {"subject_awareness": "NOT_MEASURED", "execution_interference": "NOT_MEASURED"},
        "qualifications": [],
        "non_claims": [],
        "evidence_refs": [],
        "basis": {"profile_version": "0.1", "evaluator": "t", "pinned": True},
    }
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(result))
    assert errors, "a passing relation alongside violations must not validate"


def test_result_schema_rejects_a_passing_relation_over_unmeasured_dimensions(repo_root):
    """A result whose dimensions were never measured must not report EQUIVALENT.
    Without this the schema would admit a result that measured nothing and passed."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (repo_root / "spec" / "v0.1" / "claim-preservation-result.schema.json").read_text(encoding="utf-8")
    )
    result = {
        "cpp_version": "0.1",
        "case_id": "synthetic",
        "relation": "EQUIVALENT",
        "input_claim_ref": "claim://in",
        "output_claim_ref": "claim://out",
        "dimensions": {"population_scope": {"status": "EQUIVALENT", "measurement_state": "NOT_MEASURED"}},
        "added_evidence": [],
        "violations": [],
        "observer_effect": {"subject_awareness": "NOT_MEASURED", "execution_interference": "NOT_MEASURED"},
        "qualifications": [],
        "non_claims": [],
        "evidence_refs": [],
        "basis": {"profile_version": "0.1", "evaluator": "t", "pinned": True},
    }
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(result))

    measured = json.loads(json.dumps(result))
    measured["dimensions"]["population_scope"]["measurement_state"] = "MEASURED"
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(measured)) == []


def test_result_schema_sinks_the_relation_when_any_dimension_is_amplified(repo_root):
    """The schema states this as a MUST on the relation property. It must enforce it,
    not merely describe it: the top-level violations array is not the only way an
    unsupported amplification can be recorded."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (repo_root / "spec" / "v0.1" / "claim-preservation-result.schema.json").read_text(encoding="utf-8")
    )
    result = {
        "cpp_version": "0.1",
        "case_id": "synthetic",
        "relation": "EQUIVALENT",
        "input_claim_ref": "claim://in",
        "output_claim_ref": "claim://out",
        "dimensions": {
            "causal_strength": {"status": "AMPLIFIED_UNSUPPORTED", "measurement_state": "MEASURED"},
            "population_scope": {"status": "EQUIVALENT", "measurement_state": "MEASURED"},
        },
        "added_evidence": [],
        "violations": [],
        "observer_effect": {"subject_awareness": "NO", "execution_interference": "MEASURED"},
        "qualifications": [],
        "non_claims": [],
        "evidence_refs": [],
        "basis": {"profile_version": "0.1", "evaluator": "t", "pinned": True},
    }
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(result))

    sunk = json.loads(json.dumps(result))
    sunk["relation"] = "AMPLIFIED_UNSUPPORTED"
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(sunk)) == []


def test_result_schema_blocks_unmeasured_perturbation_from_generalizing(repo_root):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (repo_root / "spec" / "v0.1" / "claim-preservation-result.schema.json").read_text(encoding="utf-8")
    )
    result = {
        "cpp_version": "0.1",
        "case_id": "synthetic",
        "relation": "EQUIVALENT",
        "input_claim_ref": "claim://in",
        "output_claim_ref": "claim://out",
        "dimensions": {"population_scope": {"status": "EQUIVALENT", "measurement_state": "MEASURED"}},
        "added_evidence": [],
        "violations": [],
        "observer_effect": {
            "subject_awareness": "UNKNOWN",
            "execution_interference": "NOT_MEASURED",
            "generalizes_to_uninstrumented": "YES",
        },
        "qualifications": [],
        "non_claims": [],
        "evidence_refs": [],
        "basis": {"profile_version": "0.1", "evaluator": "t", "pinned": True},
    }
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(result))
    assert errors, "unmeasured perturbation must not support an uninstrumented generalization"


# --- corpus quality -------------------------------------------------------


def test_positive_corpus_covers_the_required_categories(positive_fixtures):
    names = {f["name"] for f in positive_fixtures}
    required = {
        "exact_claim_preservation",
        "legitimate_scope_narrowing",
        "qualifier_preserving_summarization",
        "supported_scope_strengthening",
        "signature_claim_kept_bounded",
        "acknowledgement_not_promoted_to_effect",
        "aggregation_preserves_denominator",
        "observer_effect_qualified_result",
    }
    assert required <= names


def test_at_least_two_positives_are_near_neighbours_of_negatives(positive_fixtures, negative_fixtures):
    negative_ids = {f["id"] for f in negative_fixtures}
    neighbours = [f for f in positive_fixtures if f.get("near_neighbour_of")]
    assert len(neighbours) >= 2
    for fixture in neighbours:
        assert fixture["near_neighbour_of"] in negative_ids
        assert fixture.get("load_bearing_difference"), f"{fixture['id']} names no load-bearing difference"


def test_every_near_neighbour_declares_whether_it_is_mechanically_separable(positive_fixtures):
    """A pairing whose negative states its failure only in prose cannot demonstrate
    mechanical discrimination. Such pairs must say so rather than be counted as if
    they did."""
    for fixture in positive_fixtures:
        if not fixture.get("near_neighbour_of"):
            continue
        assert "mechanically_separable" in fixture, (
            f"{fixture['id']} claims a near-neighbour without declaring whether the pair is separable"
        )
        if fixture["mechanically_separable"] is False:
            assert fixture.get("notes"), f"{fixture['id']} must explain why the pair is not separable"


def test_at_least_six_near_neighbour_pairs_are_mechanically_separable(positive_fixtures):
    separable = [f for f in positive_fixtures if f.get("mechanically_separable") is True]
    assert len(separable) >= 6


def test_positive_fixtures_are_not_trivial(positive_fixtures, evaluations_by_id):
    """Every positive must give the evaluator something structural to decide on,
    otherwise it cannot demonstrate discrimination. `status` alone does not count:
    a fixture carrying only a status is an equality check wearing a costume."""
    for fixture in positive_fixtures:
        side = fixture.get("input", {})
        structural = [
            key
            for key in ("scope", "qualifiers", "non_claims", "population", "assurance", "states", "condition", "evidence")
            if side.get(key)
        ]
        assert len(structural) >= 2, f"{fixture['id']} carries too little structure to exercise the model"

        decided = [
            check
            for check in evaluations_by_id[fixture["id"]]["checks"]
            if check["status"] != "NOT_APPLICABLE"
        ]
        assert len(decided) >= 2, f"{fixture['id']} leaves too few checks applicable to demonstrate anything"


def test_positive_corpus_exercises_the_observer_and_evidence_requirements(evaluations_by_id, positive_fixtures):
    """Requirements that only ever appear on negative fixtures are asserted, never
    demonstrated. These four were added precisely because the first draft of the
    positive corpus never exercised them."""
    exercised: set[str] = set()
    for fixture in positive_fixtures:
        for check in evaluations_by_id[fixture["id"]]["checks"]:
            if check["status"] != "NOT_APPLICABLE":
                exercised.update(check["requirements"])
    for requirement in ("CPP-7", "CPP-12", "CPP-15", "CPP-17", "CPP-18"):
        assert requirement in exercised, f"no positive fixture exercises {requirement}"
