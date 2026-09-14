"""Tests over the reference validator's behaviour.

Two things are being established here:

1. The validator detects the claim-preservation failures it claims to detect,
   including on synthetic cases that express in structured fields what parts of
   the seed corpus express only in prose.
2. The validator does not overclaim: undecided checks stay undecided, and
   non-success states never round up into a passing relation.

The final test in this module is a mutation test: it weakens a load-bearing
rule and asserts that a detection is lost, which is what makes the rule
load-bearing rather than decorative.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

import validate
from validate import CHECKS, Fixture, derive_relation, evaluate_fixture

PASSING_RELATIONS = validate.PASSING_RELATIONS
NON_SUCCESS = {"NOT_MEASURED", "INCONCLUSIVE", "ERROR"}


def synth(**data) -> Fixture:
    data.setdefault("id", "CPP-N99")
    data.setdefault("name", "synthetic")
    data.setdefault("expected_relation", "AMPLIFIED_UNSUPPORTED")
    return Fixture(data, "synthetic")


def statuses(fx: Fixture) -> dict[str, str]:
    return {r.check: r.status for r in (check(fx) for check in CHECKS)}


# --- run validity vs claim verdict ---------------------------------------


def test_run_validity_and_claim_verdict_are_separate(repo_root, tmp_path):
    """Exit code reports whether the run was valid. The corpus contains twenty
    fixtures that are not claim-preserving, and the run still exits zero."""
    out = tmp_path / "report.json"
    proc = subprocess.run(
        [sys.executable, str(repo_root / "conformance" / "validate.py"), "--report", str(out), "--quiet"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    not_preserving = [e for e in report["evaluations"] if not e["derived_is_passing"]]
    assert len(not_preserving) >= 20
    assert report["validator"]["exit_code_meaning"].startswith("run and corpus validity only")


def test_validator_output_is_deterministic(repo_root, tmp_path):
    outputs = []
    for name in ("a.json", "b.json"):
        out = tmp_path / name
        subprocess.run(
            [sys.executable, str(repo_root / "conformance" / "validate.py"), "--report", str(out), "--quiet"],
            check=True,
            capture_output=True,
        )
        outputs.append(out.read_text(encoding="utf-8"))
    assert outputs[0] == outputs[1]


def test_validator_declares_that_semantic_entailment_is_not_implemented(report):
    assert report["validator"]["semantic_entailment"] == "NOT_IMPLEMENTED"
    assert report["summary"]["not_mechanically_decidable"], (
        "a validator that decides every case in this corpus is claiming to solve semantic entailment"
    )


def test_no_declared_relation_contradicts_the_derived_relation(report):
    assert report["summary"]["contradictions"] == []


def test_prose_only_cases_are_reported_as_undecidable_not_as_passing(evaluations_by_id):
    for case_id in ("CPP-N03", "CPP-N04", "CPP-N11", "CPP-N12", "CPP-N13", "CPP-N14"):
        evaluation = evaluations_by_id[case_id]
        assert evaluation["derived_relation"] in NON_SUCCESS
        assert evaluation["derived_is_passing"] is False
        assert evaluation["reconciliation"] == "NOT_MECHANICALLY_DECIDABLE"


def test_every_positive_fixture_is_evaluated_as_claim_preserving(evaluations_by_id, positive_fixtures):
    for fixture in positive_fixtures:
        evaluation = evaluations_by_id[fixture["id"]]
        assert evaluation["derived_relation"] == fixture["expected_relation"], fixture["id"]
        assert evaluation["derived_violations"] == []


def test_near_neighbour_pairs_are_separated_by_the_validator(evaluations_by_id, positive_fixtures):
    """A positive and its near-neighbour negative differ in one load-bearing fact.
    The validator must land them on opposite sides."""
    pairs = [
        (f["id"], f["near_neighbour_of"], f.get("mechanically_separable"))
        for f in positive_fixtures
        if f.get("near_neighbour_of")
    ]
    assert pairs
    separated = 0
    for positive_id, negative_id, claims_separable in pairs:
        positive = evaluations_by_id[positive_id]
        negative = evaluations_by_id[negative_id]
        assert positive["derived_is_passing"] is True, positive_id
        assert negative["derived_is_passing"] is False, negative_id
        mechanically_separated = negative["derived_relation"] not in NON_SUCCESS
        # A pair may not claim separability it does not have, and a pair that
        # disclaims it must genuinely be the undecidable case it says it is.
        assert mechanically_separated == bool(claims_separable), (
            f"{positive_id}/{negative_id}: mechanically_separable={claims_separable} but the validator "
            f"derived {negative['derived_relation']} for the negative"
        )
        separated += int(mechanically_separated)
    assert separated >= 6, "most near-neighbour pairs must be separated mechanically, not just asserted"


# --- the required detections ---------------------------------------------


def test_unsupported_scope_broadening_fails(evaluations_by_id):
    evaluation = evaluations_by_id["CPP-N01"]
    assert evaluation["derived_relation"] == "AMPLIFIED_UNSUPPORTED"
    assert "CPP-2" in evaluation["derived_violations"]

    fx = synth(
        input={"claim": "observed at EP-A", "scope": {"targets": ["EP-A"]}},
        output={"claim": "observed everywhere", "scope": {"targets": ["EP-A", "EP-B"]}},
        added_evidence=[],
    )
    result = statuses(fx)
    assert result["scope_monotonicity"] == "VIOLATION"


def test_supported_scope_broadening_is_allowed_when_evidence_covers_it():
    fx = synth(
        expected_relation="SUPPORTED_STRENGTHENING",
        input={"claim": "observed at EP-A", "scope": {"targets": ["EP-A"]}},
        output={"claim": "observed at EP-A and EP-B", "scope": {"targets": ["EP-A", "EP-B"]}},
        added_evidence=[{"ref": "artifact://obs-B", "covers": ["EP-B"], "supports_dimension": ["population_scope"]}],
    )
    assert statuses(fx)["scope_monotonicity"] == "SUPPORTED_STRENGTHENING"


def test_unsupported_causal_strengthening_fails(negative_fixtures):
    """CPP-N04 states the causal upgrade in prose, so the validator honestly
    reports it as undecidable. The same upgrade expressed structurally is caught."""
    n04 = next(f for f in negative_fixtures if f["id"] == "CPP-N04")
    assert n04["expected_relation"] == "AMPLIFIED_UNSUPPORTED"

    fx = synth(
        input={"claim": "control applied before the incident stopped", "condition": {"effect_state": "applied"}},
        output={"claim": "control stopped the incident", "condition": {"effect_state": "observed_effect"}},
        added_evidence=[],
    )
    assert statuses(fx)["effect_strength"] == "VIOLATION"


def test_dropped_material_non_claims_fail(evaluations_by_id):
    for case_id in ("CPP-N06", "CPP-N17"):
        evaluation = evaluations_by_id[case_id]
        assert evaluation["derived_relation"] == "AMPLIFIED_UNSUPPORTED"
        assert "CPP-4" in evaluation["derived_violations"]


def test_dropped_material_qualifiers_fail(evaluations_by_id):
    evaluation = evaluations_by_id["CPP-N05"]
    assert "CPP-3" in evaluation["derived_violations"]


def test_denominator_loss_fails(evaluations_by_id):
    for case_id in ("CPP-N09", "CPP-N10"):
        assert "CPP-11" in evaluations_by_id[case_id]["derived_violations"]

    partial = synth(
        input={"claim": "suite", "population": {"pass": 8, "error": 2, "total": 10}},
        output={"claim": "suite", "population": {"pass": 8, "error": 0, "total": 8}},
    )
    assert statuses(partial)["denominator_preservation"] == "VIOLATION"


def test_denominator_preservation_passes_when_non_success_cases_survive(evaluations_by_id):
    assert evaluations_by_id["CPP-P07"]["derived_violations"] == []


def test_self_report_to_independent_verification_upgrade_fails(negative_fixtures):
    n14 = next(f for f in negative_fixtures if f["id"] == "CPP-N14")
    assert n14["expected_relation"] == "AMPLIFIED_UNSUPPORTED"

    fx = synth(
        input={"claim": "agent reports success", "assurance": "SELF_ASSERTED"},
        output={"claim": "independently observed success", "assurance": "INDEPENDENT_OBSERVER"},
        added_evidence=[],
    )
    assert statuses(fx)["assurance_independence"] == "VIOLATION"


def test_acknowledgement_to_effect_upgrade_fails(negative_fixtures):
    n13 = next(f for f in negative_fixtures if f["id"] == "CPP-N13")
    assert n13["expected_relation"] == "AMPLIFIED_UNSUPPORTED"

    fx = synth(
        input={"claim": "receiver acknowledged I", "condition": {"effect_state": "acknowledged"}},
        output={"claim": "I achieved its effect", "condition": {"effect_state": "observed_effect"}},
        added_evidence=[],
    )
    assert statuses(fx)["effect_strength"] == "VIOLATION"


def test_signature_integrity_to_truth_upgrade_fails(negative_fixtures):
    """Integrity establishes the record, not the recorded fact. Structurally, the
    upgrade shows up as the integrity non-claim disappearing downstream."""
    n12 = next(f for f in negative_fixtures if f["id"] == "CPP-N12")
    assert n12["expected_relation"] == "AMPLIFIED_UNSUPPORTED"

    fx = synth(
        input={
            "claim": "record R has a valid signature under key K",
            "assurance": "KEY_ATTRIBUTED",
            "non_claims": ["Does not establish that the event recorded in R occurred."],
        },
        output={
            "claim": "the event recorded in R occurred",
            "assurance": "INDEPENDENT_OBSERVER",
            "non_claims": [],
        },
        added_evidence=[],
    )
    result = statuses(fx)
    assert result["non_claim_preservation"] == "VIOLATION"
    assert result["assurance_independence"] == "VIOLATION"


def test_unverified_evidence_must_not_be_presented_as_verified():
    fx = synth(
        input={"claim": "E1", "evidence": [{"ref": "artifact://E1", "resolvable": False, "verified": False}]},
        output={"claim": "E1 independently verified", "assurance": "INDEPENDENT_OBSERVER"},
    )
    assert statuses(fx)["evidence_resolvability"] == "VIOLATION"


def test_observer_perturbation_generalization_fails(evaluations_by_id):
    evaluation = evaluations_by_id["CPP-N18"]
    assert "CPP-15" in evaluation["derived_violations"]

    fx = synth(
        input={"claim": "measured under tracing"},
        output={"claim": "uninstrumented rate", "condition": {"generalizes_to": "uninstrumented"}},
        observer_effect={"subject_awareness": "NO", "execution_interference": "NOT_MEASURED"},
    )
    assert statuses(fx)["uninstrumented_generalization"] == "VIOLATION"


def test_observer_perturbation_disclosure_passes_when_overhead_is_measured(evaluations_by_id):
    assert evaluations_by_id["CPP-P08"]["derived_violations"] == []


def test_evaluation_awareness_generalization_fails(evaluations_by_id):
    evaluation = evaluations_by_id["CPP-N19"]
    assert "CPP-17" in evaluation["derived_violations"]


def test_semantic_state_collapse_fails_and_preserved_distinctions_pass(evaluations_by_id):
    assert "CPP-12" in evaluations_by_id["CPP-N15"]["derived_violations"]
    assert evaluations_by_id["CPP-P09"]["derived_violations"] == []


def test_mutable_basis_cannot_support_a_frozen_reproducibility_claim(evaluations_by_id):
    assert "CPP-13" in evaluations_by_id["CPP-N16"]["derived_violations"]


def test_silent_evidence_sink_failure_cannot_produce_positive_assurance(evaluations_by_id):
    evaluation = evaluations_by_id["CPP-N20"]
    assert evaluation["derived_relation"] == "AMPLIFIED_UNSUPPORTED"
    assert {"CPP-18", "CPP-5"} <= set(evaluation["derived_violations"])
    assert evaluation["derived_is_passing"] is False


# --- non-success states may not collapse ---------------------------------


@pytest.mark.parametrize("status", ["NOT_MEASURED", "INCONCLUSIVE", "ERROR", "WITHHELD"])
def test_non_success_status_cannot_become_a_pass(status):
    fx = synth(input={"claim": "c", "status": status}, output={"claim": "c", "status": "PASS"})
    assert statuses(fx)["status_non_success_preservation"] == "VIOLATION"
    assert evaluate_fixture(fx)["derived_is_passing"] is False


@pytest.mark.parametrize("status", ["NOT_MEASURED", "INCONCLUSIVE", "ERROR"])
def test_non_success_status_survives_when_preserved(status):
    fx = synth(
        expected_relation="EQUIVALENT",
        id="CPP-P99",
        input={"claim": "c", "status": status, "qualifiers": ["q"]},
        output={"claim": "c", "status": status, "qualifiers": ["q"]},
    )
    assert evaluate_fixture(fx)["derived_relation"] == "EQUIVALENT"


@pytest.mark.parametrize("undecided", ["NOT_MEASURED", "INCONCLUSIVE"])
def test_an_undecided_check_can_never_round_up_to_a_passing_relation(undecided):
    results = [
        validate.CheckResult("decided", ["CPP-2"], validate.PRESERVING, "", ""),
        validate.CheckResult("undecided", ["CPP-7"], undecided, "", ""),
    ]
    assert derive_relation(results) not in PASSING_RELATIONS


def test_a_violation_dominates_any_number_of_preserving_checks():
    results = [validate.CheckResult(f"ok{i}", ["CPP-2"], validate.PRESERVING, "", "") for i in range(10)]
    results.append(validate.CheckResult("bad", ["CPP-5"], validate.VIOLATION, "", ""))
    assert derive_relation(results) == "AMPLIFIED_UNSUPPORTED"


def test_a_fixture_with_no_applicable_checks_is_not_measured_rather_than_equivalent():
    fx = synth(input={"claim": "prose only"}, output={"claim": "different prose"})
    evaluation = evaluate_fixture(fx)
    assert evaluation["derived_relation"] == "NOT_MEASURED"
    assert evaluation["derived_is_passing"] is False


# --- regression: checks must not report PRESERVING on facts they never examined ---
#
# Each of these was a real collapse path found in review: a check returned
# PRESERVING (reported as measurement_state MEASURED) for a transformation it had
# not actually evaluated, and the fixture came out EQUIVALENT. They are pinned here
# because the failure mode is silent by construction.


def test_sink_failure_with_no_emitted_status_is_not_preserving():
    """CPP-18 requires a distinguishable non-success state to be emitted. Emitting
    no status at all is the violation, not an absence of one."""
    fx = synth(observer={"evidence_sink_write": "FAILED_SILENTLY"}, input={"claim": "x"}, output={"claim": "x"})
    assert statuses(fx)["evidence_sink_integrity"] == "VIOLATION"
    assert evaluate_fixture(fx)["derived_is_passing"] is False


def test_sink_failure_with_an_out_of_vocabulary_status_is_inconclusive():
    fx = synth(
        observer={"evidence_sink_write": "FAILED_SILENTLY"},
        input={"claim": "x"},
        output={"claim": "x", "status": "GREEN"},
    )
    assert statuses(fx)["evidence_sink_integrity"] == "INCONCLUSIVE"
    assert evaluate_fixture(fx)["derived_is_passing"] is False


def test_sink_failure_reported_as_a_non_success_status_is_preserving():
    fx = synth(
        expected_relation="NARROWER",
        observer={"evidence_sink_write": "FAILED"},
        input={"claim": "x", "status": "PASS"},
        output={"claim": "x", "status": "ERROR"},
    )
    assert statuses(fx)["evidence_sink_integrity"] == "PRESERVING"


def test_replacing_a_pinned_basis_with_a_moving_one_fails():
    """The profile names this at 7.2: 'replacing a pinned basis with a mutable
    latest basis'. Judging only the input basis would miss it."""
    fx = synth(
        input={"claim": "x", "basis": "spec@sha256:3f1c0b"},
        output={"claim": "x", "basis": "https://example.org/spec/latest"},
    )
    assert statuses(fx)["basis_pinning"] == "VIOLATION"
    assert evaluate_fixture(fx)["derived_is_passing"] is False


def test_dropping_the_basis_entirely_fails():
    fx = synth(input={"claim": "x", "basis": "spec@sha256:3f1c0b"}, output={"claim": "x"})
    assert statuses(fx)["basis_pinning"] == "VIOLATION"


def test_dropped_system_boundary_fails():
    fx = synth(
        input={"claim": "x", "scope": {"targets": ["EP-A"], "boundary": "instrumented runtime"}},
        output={"claim": "x", "scope": {"targets": ["EP-A"]}},
    )
    assert statuses(fx)["scope_monotonicity"] == "VIOLATION"


def test_an_unaccounted_denominator_is_inconclusive_not_preserving():
    """A population declaring total 10 while enumerating 8 has two cases whose
    disposition is unknown. That is not a clean population."""
    fx = synth(input={"claim": "x", "population": {"pass": 8, "total": 10}}, output={"claim": "x"})
    assert statuses(fx)["denominator_preservation"] == "INCONCLUSIVE"
    assert evaluate_fixture(fx)["derived_is_passing"] is False


def test_unmeasured_generalization_is_reported_as_unmeasured():
    fx = synth(
        input={"claim": "x"},
        output={"claim": "x"},
        observer_effect={"execution_interference": "MEASURED", "generalizes_to_uninstrumented": "NOT_MEASURED"},
    )
    result = [r for r in (check(fx) for check in CHECKS) if r.check == "uninstrumented_generalization"][0]
    assert result.status == "NOT_MEASURED"
    assert result.to_dict()["measurement_state"] == "NOT_MEASURED"


def test_no_check_reports_measured_without_examining_both_sides(report):
    """Across the whole corpus, every check that reports a measured outcome must
    have produced a detail string describing what it compared."""
    for evaluation in report["evaluations"]:
        for check in evaluation["checks"]:
            if check["measurement_state"] == "MEASURED":
                assert check["detail"].strip(), f"{evaluation['case_id']}/{check['check']} reports MEASURED with no detail"
                assert check["basis"].strip(), f"{evaluation['case_id']}/{check['check']} reports MEASURED with no basis"


def test_coverage_reports_what_was_not_evaluated(evaluations_by_id):
    """A result must not imply that unexamined requirements were satisfied."""
    evaluation = evaluations_by_id["CPP-P01"]
    assert evaluation["coverage"]["not_evaluated"], "coverage must record the requirements it did not examine"
    assert set(evaluation["coverage"]["evaluated"]) & set(evaluation["coverage"]["not_evaluated"]) == set()


# --- mutation tests -------------------------------------------------------


def test_mutating_the_status_rule_loses_a_detection(negative_fixtures):
    """Weaken the CPP-5 rule so a non-success status may become a PASS. If the
    corpus still reported the same result, the rule would not be load-bearing
    and the CPP-N07 detection would be an accident."""
    n07 = Fixture(next(f for f in negative_fixtures if f["id"] == "CPP-N07"), "negative")

    baseline = evaluate_fixture(n07)
    assert baseline["derived_relation"] == "AMPLIFIED_UNSUPPORTED"
    assert "CPP-5" in baseline["derived_violations"]

    def weakened(fx):
        """Mutant: treat any status transition as preserving."""
        return validate.CheckResult(
            "status_non_success_preservation",
            ["CPP-5"],
            validate.PRESERVING,
            "mutant: status transitions accepted unconditionally",
            "mutant",
        )

    mutated_checks = tuple(weakened if c is validate.check_status_preservation else c for c in CHECKS)
    mutant = evaluate_fixture(n07, checks=mutated_checks)

    assert mutant["derived_relation"] != "AMPLIFIED_UNSUPPORTED"
    assert "CPP-5" not in mutant["derived_violations"]
    assert mutant["derived_relation"] in PASSING_RELATIONS, (
        "the mutant should wrongly accept CPP-N07, which is exactly the failure the real rule prevents"
    )


def test_mutating_the_denominator_rule_loses_a_detection(negative_fixtures):
    n09 = Fixture(next(f for f in negative_fixtures if f["id"] == "CPP-N09"), "negative")
    assert "CPP-11" in evaluate_fixture(n09)["derived_violations"]

    def weakened(fx):
        """Mutant: accept a missing output population as preservation."""
        source = fx.input.get("population")
        if not isinstance(source, dict):
            return validate._na("denominator_preservation", ["CPP-11"], "no input population")
        return validate.CheckResult(
            "denominator_preservation", ["CPP-11"], validate.PRESERVING, "mutant", "mutant"
        )

    mutated_checks = tuple(weakened if c is validate.check_denominator else c for c in CHECKS)
    mutant = evaluate_fixture(n09, checks=mutated_checks)
    assert "CPP-11" not in mutant["derived_violations"]
    assert mutant["derived_relation"] in PASSING_RELATIONS


def test_mutating_the_composition_rule_lets_the_prose_only_negatives_pass(negative_fixtures):
    """Weaken the composition rule so anything without an outright violation reports
    EQUIVALENT, and run it over the six negatives the validator honestly cannot
    decide. Under the mutant every one of them is reported as claim-preserving,
    which is what the real precedence order prevents."""
    prose_only = ("CPP-N03", "CPP-N04", "CPP-N11", "CPP-N12", "CPP-N13", "CPP-N14")
    fixtures = [Fixture(f, "negative") for f in negative_fixtures if f["id"] in prose_only]
    assert len(fixtures) == len(prose_only)

    for fx in fixtures:
        assert evaluate_fixture(fx)["derived_is_passing"] is False

    original = validate.derive_relation

    def mutant(check_results):
        """Mutant: treat 'no violation found' as 'claim preserved'."""
        if validate.CHECK_ERROR in {r.status for r in check_results}:
            return "ERROR"
        if validate.VIOLATION in {r.status for r in check_results}:
            return "AMPLIFIED_UNSUPPORTED"
        return "EQUIVALENT"

    validate.derive_relation = mutant
    try:
        mutated = [evaluate_fixture(fx) for fx in fixtures]
    finally:
        validate.derive_relation = original

    assert all(e["derived_relation"] == "EQUIVALENT" for e in mutated)
    assert all(e["derived_is_passing"] is True for e in mutated)
    assert all(e["reconciliation"] == "CONTRADICTS" for e in mutated), (
        "under the mutant these six would contradict their declared relation, which is exactly "
        "the signal the real precedence order exists to avoid producing"
    )

    # And the real rule is restored and still correct.
    assert derive_relation(
        [
            validate.CheckResult("decided", ["CPP-2"], validate.PRESERVING, "d", "b"),
            validate.CheckResult("undecided", ["CPP-7"], validate.INCONCLUSIVE, "d", "b"),
        ]
    ) == "INCONCLUSIVE"
