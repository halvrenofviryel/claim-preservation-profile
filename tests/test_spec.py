"""Tests over the profile text itself.

These guard the parts of CPP v0.1 that the rest of the repository depends on,
and the claim-accuracy boundaries the repository commits to.
"""

from __future__ import annotations

import re

import pytest
import yaml

RELATIONS = [
    "EQUIVALENT",
    "NARROWER",
    "SUPPORTED_STRENGTHENING",
    "AMPLIFIED_UNSUPPORTED",
    "INCOMPARABLE",
    "NOT_MEASURED",
    "INCONCLUSIVE",
    "ERROR",
]


def test_twenty_requirements_are_defined(spec_text):
    found = re.findall(r"^###\s+(CPP-\d+)\s+—", spec_text, flags=re.MULTILINE)
    assert found == [f"CPP-{n}" for n in range(1, 21)]


def test_central_invariant_is_present_and_complete(spec_text):
    match = re.search(r"A transformation MUST NOT increase[^.]+\.", spec_text)
    assert match, "the central invariant sentence is missing"
    invariant = match.group(0)
    for dimension in (
        "semantic strength",
        "scope",
        "certainty",
        "causal implication",
        "independence claim",
        "completeness claim",
        "assurance level",
    ):
        assert dimension in invariant, f"{dimension!r} missing from the central invariant"
    assert "identifiable additional evidence" in invariant
    assert "sufficient for that increase" in invariant


def test_claim_model_is_intact(spec_text):
    assert "`C = (P, S, Q, N, E, A, V)`" in spec_text
    for symbol, meaning in (
        ("`P`", "proposition"),
        ("`S`", "scope"),
        ("`Q`", "qualifiers"),
        ("`N`", "non-claims"),
        ("`E`", "evidence"),
        ("`A`", "assurance attributes"),
        ("`V`", "observation validity"),
    ):
        assert re.search(rf"- {re.escape(symbol)} — {meaning}", spec_text, flags=re.IGNORECASE), (
            f"claim-model component {symbol} ({meaning}) missing"
        )


@pytest.mark.parametrize("relation", RELATIONS)
def test_relation_vocabulary_is_intact(spec_text, relation):
    assert f"`{relation}`" in spec_text


def test_no_scalar_claim_strength_score(spec_text):
    assert "does not require one scalar" in spec_text
    assert "partial order over independent dimensions" in spec_text


def test_non_success_states_may_not_collapse(spec_text):
    assert (
        "`NOT_MEASURED`, `INCONCLUSIVE`, and `ERROR` MUST NOT be collapsed to `EQUIVALENT`, "
        "`NARROWER`, or any passing state." in spec_text
    )


def test_observer_effect_is_in_scope_with_both_channels(spec_text):
    assert "## 7. Observer/probe-effect extension" in spec_text
    assert "### 7.1 Runtime perturbation" in spec_text
    assert "### 7.2 Semantic perturbation" in spec_text
    for runtime_signal in ("latency", "scheduling", "timeout", "buffering", "permissions", "control flow"):
        assert runtime_signal in spec_text
    for semantic_signal in ("collapsing distinct states", "denominators", "self-report"):
        assert semantic_signal in spec_text


def test_observer_effect_is_not_framed_as_quantum_uncertainty(spec_text):
    assert "not as a statement of quantum mechanics" in spec_text
    assert "is not derived from, and does not depend on, the Heisenberg uncertainty principle" in spec_text
    assert "at most a loose analogy" in spec_text


def test_integrity_is_not_truth_and_observation_is_not_effect(spec_text):
    assert "### CPP-8 — Integrity is not truth" in spec_text
    assert "### CPP-9 — Observation is not effect" in spec_text
    assert "MUST NOT by themselves upgrade a claim" in spec_text


def test_conformance_verdict_is_bounded(spec_text):
    assert (
        "not about whether the underlying AI system is safe, correct, aligned, or compliant" in spec_text
    )


def test_spec_declares_experimental_author_proposal_status(spec_text):
    assert "**Status:** Experimental technical profile" in spec_text
    assert "**Normative status:** Author proposal" in spec_text
    assert "Not a standard, not adopted, not independently reviewed, not independently reproduced." in spec_text


def test_spec_does_not_claim_adoption_or_ownership_of_neighbouring_work(spec_text):
    assert "CPP is not an AIREP profile." in spec_text
    assert "CPP does not alter AIREP conformance" in spec_text
    assert "does not modify Measurement Axioms v1.0" in spec_text
    assert "or CDE-12" in spec_text
    assert "not evidence of IETF" in spec_text
    assert "working-group review, adoption, consensus, or endorsement" in spec_text
    forbidden = [
        "industry standard",
        "adopted standard",
        "consensus-backed",
        "independently validated",
        "independently reproduced by",
    ]
    lowered = spec_text.lower()
    for phrase in forbidden:
        assert phrase not in lowered, f"spec contains overclaiming phrase {phrase!r}"


def test_status_file_states_the_required_facts(repo_root):
    status = (repo_root / "STATUS.md").read_text(encoding="utf-8")
    for line in (
        "version: 0.1",
        "status: EXPERIMENTAL",
        "normative_status: author proposal",
        "independent_review: NOT_REQUESTED",
        "independent_reproduction: NOT_MEASURED",
        "deployment_evidence: NOT_MEASURED",
        "standardization_status: NONE",
        "conformance_claims: none",
    ):
        assert line in status, f"STATUS.md is missing {line!r}"
    assert "author-created research artifacts" in status
    assert "not independent empirical validation" in status


def test_citation_metadata_parses_and_pins_verified_identifiers(repo_root):
    citation = yaml.safe_load((repo_root / "CITATION.cff").read_text(encoding="utf-8"))
    assert "date-released" not in citation, "the unreleased CPP candidate must not claim a release date"
    assert citation["authors"] == [
        {
            "family-names": "Abak",
            "given-names": "Ali Toygar",
            "affiliation": "Phionyx",
            "orcid": "https://orcid.org/0009-0002-3718-4010",
        }
    ]
    paper = citation["references"][0]
    assert paper["url"] == "https://huggingface.co/blog/phionyx/access-is-not-yet-verifiability"
    assert paper["date-published"] == "2026-09-13"
    assert paper["doi"] == "10.5281/zenodo.22754297"
    assert paper["authors"][0]["orcid"] == "https://orcid.org/0009-0002-3718-4010"
