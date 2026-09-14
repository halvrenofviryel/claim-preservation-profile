#!/usr/bin/env python3
"""CPP v0.1 reference conformance validator.

What this program is
--------------------
It does two separate things, and keeps them separate on purpose:

1. **Corpus validation** — is the fixture corpus itself well formed? Shape,
   unique ids, legal relation values, requirement ids that actually exist in
   the profile text.

2. **Claim-relation evaluation** — for each fixture, derive a claim relation
   from the *structured* fields of the fixture, independently of the relation
   the fixture declares, and then reconcile the two.

What this program deliberately does not do
------------------------------------------
It does not decide natural-language semantic entailment. Where the
load-bearing fact of a case exists only in prose, the affected check returns
``NOT_MEASURED`` or ``INCONCLUSIVE`` and the derived relation is a non-success
state. No check infers a passing outcome from prose: each check decides only over
the structured fields it actually compares, and an undecided check never rounds up
into a claim-preserving relation.

Exit codes (run validity, not claim verdicts)
---------------------------------------------
The process exit code reports whether the *run* was valid. It does not report
whether the claims passed. Claim-preservation verdicts live in the report body.

  0  run completed and the corpus is structurally valid
  2  run could not be performed (bad arguments, unreadable or unparseable input)
  3  run completed but the corpus is structurally invalid
  4  policy gate: --fail-on-contradiction was given and at least one fixture's
     declared relation contradicts the derived relation
  5  run incomplete: a required check could not be executed (for example
     JSON Schema validation with `jsonschema` not installed)

A zero exit therefore means "this run was valid and the corpus is well formed".
It does not mean "every claim was preserved".

Determinism and isolation
-------------------------
Output is a deterministic function of the input files: keys are sorted, no
wall-clock time, no randomness, no network access, no environment lookups
beyond argument parsing. The only optional dependency is ``jsonschema``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

CPP_VERSION = "0.1"
VALIDATOR_VERSION = "0.1.1"

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC = REPO_ROOT / "spec" / "v0.1" / "CLAIM_PRESERVATION_PROFILE.md"
DEFAULT_CONFORMANCE = REPO_ROOT / "conformance"

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------

RELATIONS = (
    "EQUIVALENT",
    "NARROWER",
    "SUPPORTED_STRENGTHENING",
    "AMPLIFIED_UNSUPPORTED",
    "INCOMPARABLE",
    "NOT_MEASURED",
    "INCONCLUSIVE",
    "ERROR",
)

#: Relations that may be treated as claim-preserving. Everything else is not.
PASSING_RELATIONS = frozenset({"EQUIVALENT", "NARROWER", "SUPPORTED_STRENGTHENING"})

#: Relations that record the absence of a decision. These are never passing.
UNDECIDED_RELATIONS = frozenset({"NOT_MEASURED", "INCONCLUSIVE"})

#: Statuses a pipeline stage may emit that are not successes.
NON_SUCCESS_STATUSES = frozenset(
    {
        "NOT_MEASURED",
        "INCONCLUSIVE",
        "ERROR",
        "WITHHELD",
        "UNRESOLVED",
        "TIMEOUT",
        "DEFER",
        "DENY",
        "FAILED",
        "FAIL",
        "SKIPPED",
    }
)

#: Statuses that read downstream as a success.
PASSING_STATUSES = frozenset({"PASS", "PASSED", "VERIFIED", "SUCCESS", "OK", "CONFORMANT"})

#: Assurance independence ladder (CPP-10). Higher is a stronger independence claim.
ASSURANCE_RANK = {
    "UNKNOWN": -1,
    "SELF_ASSERTED": 0,
    "SAME_PROCESS_CHECKED": 1,
    "INTEGRITY_CHECKED": 2,
    "KEY_ATTRIBUTED": 2,
    "INDEPENDENT_OBSERVER": 3,
    "INDEPENDENT_REPLAY": 4,
}

#: Execution/effect ladder (CPP-9).
EFFECT_RANK = {
    "issued": 0,
    "received": 1,
    "acknowledged": 2,
    "accepted": 2,
    "applied": 3,
    "enforced": 3,
    "observed_effect": 4,
    "independently_observed_effect": 5,
}

#: Tokens that make a basis reference moving rather than pinned (CPP-13).
MOVING_BASIS_TOKENS = ("latest", "main", "master", "head", "current", "newest", "stable")

# Check outcome vocabulary.
PRESERVING = "PRESERVING"
NARROWING = "NARROWING"
STRENGTHENING_SUPPORTED = "SUPPORTED_STRENGTHENING"
VIOLATION = "VIOLATION"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_MEASURED = "NOT_MEASURED"
INCONCLUSIVE = "INCONCLUSIVE"
CHECK_ERROR = "ERROR"

MEASUREMENT_STATE = {
    PRESERVING: "MEASURED",
    NARROWING: "MEASURED",
    STRENGTHENING_SUPPORTED: "MEASURED",
    VIOLATION: "MEASURED",
    NOT_APPLICABLE: "NOT_APPLICABLE",
    NOT_MEASURED: "NOT_MEASURED",
    INCONCLUSIVE: "INCONCLUSIVE",
    CHECK_ERROR: "ERROR",
}

#: Documented modelling assumption. A fixture is treated as a complete
#: representation of what the stage emits, so a field absent from the output
#: side is treated as not emitted rather than as unknown. CPP-4 makes this
#: explicit for non-claims: absence is not discharge.
COMPLETENESS_ASSUMPTION = (
    "Fixtures are read as complete representations of what the stage emits: a field "
    "absent from the output side is treated as not emitted, not as unknown."
)


class RunError(Exception):
    """The run itself could not be performed."""


# --------------------------------------------------------------------------
# Normalisation: canonical layout plus the v0.1 flat aliases
# --------------------------------------------------------------------------


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _evidence_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _as_list(value):
        if isinstance(item, str):
            items.append({"ref": item})
        elif isinstance(item, dict):
            items.append(item)
    return items


class Side:
    """One side of a transformation, after alias normalisation."""

    __slots__ = ("raw", "present")

    def __init__(self, raw: dict[str, Any], present: set[str]) -> None:
        self.raw = raw
        self.present = present

    def has(self, field: str) -> bool:
        return field in self.present

    def get(self, field: str, default: Any = None) -> Any:
        return self.raw.get(field, default)


def _build_side(canonical: dict[str, Any], aliases: dict[str, Any]) -> Side:
    raw: dict[str, Any] = {}
    present: set[str] = set()
    for field, value in list(canonical.items()) + list(aliases.items()):
        if value is None:
            continue
        raw[field] = value
        present.add(field)
    return Side(raw, present)


class Fixture:
    """A normalised fixture."""

    def __init__(self, data: dict[str, Any], corpus: str) -> None:
        self.data = data
        self.corpus = corpus
        self.id = data.get("id")
        self.name = data.get("name")
        self.declared_relation = data.get("expected_relation")
        self.declared_violations = sorted(
            set(_as_list(data.get("expected_violations")) + _as_list(data.get("violates")))
        )

        canonical_in = dict(data.get("input") or {})
        alias_in = {
            "claim": data.get("input_claim"),
            "status": data.get("input_status"),
            "scope": data.get("input_scope"),
            "qualifiers": data.get("input_qualifiers"),
            "non_claims": data.get("input_nonclaims"),
            "population": data.get("input_population"),
            "evidence": data.get("input_evidence"),
            "basis": data.get("input_basis"),
            "states": data.get("input_states"),
        }
        self.input = _build_side(canonical_in, alias_in)

        canonical_out = dict(data.get("output") or {})
        alias_out = {
            "claim": data.get("bad_output_claim"),
            "status": data.get("bad_output_status"),
            "non_claims": data.get("bad_output_nonclaims"),
            "qualifiers": data.get("bad_output_qualifiers"),
            "population": data.get("bad_output_population"),
        }
        self.output = _build_side(canonical_out, alias_out)

        transformation = dict(data.get("transformation") or {})
        if data.get("adapter_mapping") is not None:
            transformation.setdefault("mapping", data["adapter_mapping"])
        if data.get("redaction") is not None:
            transformation.setdefault("kind", "redact")
            transformation.setdefault("description", data["redaction"])
        self.transformation = transformation

        self.added_evidence = _evidence_items(data.get("added_evidence"))
        self.observer_effect = data.get("observer_effect") or {}
        self.observation_intervention = data.get("observation_intervention") or {}
        self.sampling_accounting = data.get("sampling_accounting") or {}
        self.observer = data.get("observer") or {}
        self.baseline = data.get("baseline") or {}
        self.instrumented = data.get("instrumented") or {}
        self.evaluation_condition = data.get("evaluation_condition") or {}
        self.deployment_condition = data.get("deployment_condition") or {}

    # helpers -------------------------------------------------------------

    def evidence_supporting(self, dimension: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self.added_evidence
            if dimension in _as_list(item.get("supports_dimension"))
        ]

    def evidence_covering(self, target: str) -> list[dict[str, Any]]:
        return [item for item in self.added_evidence if target in _as_list(item.get("covers"))]


# --------------------------------------------------------------------------
# Check results
# --------------------------------------------------------------------------


class CheckResult:
    __slots__ = ("check", "requirements", "status", "detail", "basis")

    def __init__(
        self,
        check: str,
        requirements: list[str],
        status: str,
        detail: str,
        basis: str,
    ) -> None:
        self.check = check
        self.requirements = requirements
        self.status = status
        self.detail = detail
        self.basis = basis

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "requirements": self.requirements,
            "status": self.status,
            "measurement_state": MEASUREMENT_STATE[self.status],
            "detail": self.detail,
            "basis": self.basis,
        }


def _na(check: str, requirements: list[str], why: str) -> CheckResult:
    return CheckResult(check, requirements, NOT_APPLICABLE, why, "structural precondition absent")


# --------------------------------------------------------------------------
# Checks. Each is a pure function of one normalised fixture.
# --------------------------------------------------------------------------


def check_status_preservation(fx: Fixture) -> CheckResult:
    name, req = "status_non_success_preservation", ["CPP-5"]
    if not (fx.input.has("status") and fx.output.has("status")):
        return _na(name, req, "input or output status not represented")
    src = str(fx.input.get("status")).upper()
    dst = str(fx.output.get("status")).upper()
    if src in NON_SUCCESS_STATUSES and dst in PASSING_STATUSES:
        if fx.added_evidence:
            return CheckResult(
                name,
                req,
                INCONCLUSIVE,
                f"status moved from non-success {src} to {dst} and added evidence is present, "
                "but whether that evidence establishes the success is not mechanically decidable",
                "status ladder plus added-evidence presence",
            )
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"non-success status {src} became {dst} with no added evidence",
            "CPP-5: NOT_MEASURED, INCONCLUSIVE, ERROR and withheld states must remain distinguishable downstream",
        )
    if src == dst:
        return CheckResult(name, req, PRESERVING, f"status unchanged ({src})", "exact status comparison")
    if src in PASSING_STATUSES and dst in NON_SUCCESS_STATUSES:
        return CheckResult(name, req, NARROWING, f"status weakened from {src} to {dst}", "status ladder")
    return CheckResult(
        name,
        req,
        INCONCLUSIVE,
        f"status changed from {src} to {dst}; neither value is in the known success/non-success vocabulary",
        "status ladder",
    )


def check_evidence_sink(fx: Fixture) -> CheckResult:
    name, req = "evidence_sink_integrity", ["CPP-18", "CPP-5"]
    sink = fx.observer.get("evidence_sink_write")
    if sink is None:
        return _na(name, req, "no evidence-sink state represented")
    failed = "FAIL" in str(sink).upper()
    if not failed:
        return CheckResult(name, req, PRESERVING, f"evidence sink write is {sink}", "CPP-18")

    if not fx.output.has("status"):
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"evidence sink write is {sink} and the output emits no status at all, so the "
            "recording failure is not distinguishable downstream",
            f"CPP-18: the pipeline must emit a distinguishable non-success state. {COMPLETENESS_ASSUMPTION}",
        )
    dst = str(fx.output.get("status")).upper()
    if dst in PASSING_STATUSES:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"evidence sink write is {sink} yet the emitted status is {dst}",
            "CPP-18: silent recording failure must not produce a positive assurance result",
        )
    if dst in NON_SUCCESS_STATUSES:
        return CheckResult(
            name,
            req,
            PRESERVING,
            f"evidence sink write is {sink} and the emitted status {dst} is a distinguishable non-success state",
            "CPP-18",
        )
    return CheckResult(
        name,
        req,
        INCONCLUSIVE,
        f"evidence sink write is {sink} and the emitted status {dst} is in neither the success nor the "
        "non-success vocabulary, so whether the failure is distinguishable downstream cannot be decided",
        "CPP-18",
    )


def _population_non_success(pop: dict[str, Any]) -> dict[str, int]:
    return {
        key: int(value)
        for key, value in pop.items()
        if key not in ("pass", "total") and isinstance(value, int) and value > 0
    }


def check_denominator(fx: Fixture) -> CheckResult:
    name, req = "denominator_preservation", ["CPP-11"]
    src = fx.input.get("population")
    if not isinstance(src, dict):
        return _na(name, req, "no input population represented")
    non_success = _population_non_success(src)
    enumerated = sum(v for k, v in src.items() if k != "total" and isinstance(v, int) and not isinstance(v, bool))
    declared_total = src.get("total")
    if isinstance(declared_total, int) and declared_total > enumerated:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"input population declares total {declared_total} but the enumerated buckets sum to {enumerated}; "
            f"{declared_total - enumerated} cases are unaccounted for and their disposition cannot be decided",
            "CPP-11: the denominator construction must be represented before preservation can be evaluated",
        )
    dst = fx.output.get("population")
    if not non_success:
        if not isinstance(dst, dict):
            return CheckResult(
                name,
                req,
                NOT_MEASURED,
                "input population has no non-success cases and the output emits no population, "
                "so denominator preservation was not evaluated",
                "CPP-11",
            )
        if int(dst.get("total", 0) or 0) < int(declared_total or 0):
            return CheckResult(
                name,
                req,
                VIOLATION,
                f"output denominator {dst.get('total')} is smaller than the input denominator {declared_total}",
                "CPP-11",
            )
        return CheckResult(name, req, PRESERVING, "input population has no non-success cases and the denominator is preserved", "population arithmetic")
    if not isinstance(dst, dict):
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"input population carries non-success cases {sorted(non_success.items())} "
            "but the output emits no population, so those cases are not visible downstream",
            f"CPP-11: aggregation must preserve the assessed, excluded and unmeasured populations. {COMPLETENESS_ASSUMPTION}",
        )
    lost = {
        key: value for key, value in non_success.items() if int(dst.get(key, 0) or 0) < value
    }
    if lost:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"non-success cases shrank or disappeared in the output population: {sorted(lost.items())}",
            "CPP-11: dropped, errored and withheld cases must not silently leave the denominator",
        )
    if int(dst.get("total", 0) or 0) < int(src.get("total", 0) or 0):
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"output denominator {dst.get('total')} is smaller than the input denominator {src.get('total')}",
            "CPP-11",
        )
    return CheckResult(name, req, PRESERVING, "non-success populations and denominator preserved", "population arithmetic")


def _preservation_of_list(
    fx: Fixture,
    name: str,
    req: list[str],
    field: str,
    label: str,
    rationale: str,
) -> CheckResult:
    src = _as_list(fx.input.get(field))
    if not src:
        return _na(name, req, f"input carries no {label}")
    dst = _as_list(fx.output.get(field))
    missing = [item for item in src if item not in dst]
    if not missing:
        return CheckResult(name, req, PRESERVING, f"all input {label} present in the output", "set comparison")
    discharged = [item for item in fx.added_evidence if _as_list(item.get("discharges"))]
    if discharged:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"{label} missing from the output ({missing}) while added evidence claims discharge; "
            "whether the discharge is sufficient is not mechanically decidable",
            rationale,
        )
    if fx.added_evidence:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"{label} missing from the output ({missing}); added evidence is present but names no discharge",
            rationale,
        )
    return CheckResult(
        name,
        req,
        VIOLATION,
        f"{label} dropped with no added evidence discharging them: {missing}",
        f"{rationale} {COMPLETENESS_ASSUMPTION}",
    )


def check_non_claims(fx: Fixture) -> CheckResult:
    return _preservation_of_list(
        fx,
        "non_claim_preservation",
        ["CPP-4"],
        "non_claims",
        "non-claims",
        "CPP-4: a relevant non-claim must remain visible unless explicitly discharged by added evidence, "
        "and absence of a non-claim field must not be read as discharge.",
    )


def check_qualifiers(fx: Fixture) -> CheckResult:
    return _preservation_of_list(
        fx,
        "qualifier_preservation",
        ["CPP-3"],
        "qualifiers",
        "qualifiers",
        "CPP-3: qualifiers relevant to the output claim must be preserved unless each removed qualifier "
        "is explicitly discharged by added evidence.",
    )


def check_scope(fx: Fixture) -> CheckResult:
    name, req = "scope_monotonicity", ["CPP-2"]
    src = fx.input.get("scope")
    if not isinstance(src, dict) or not src:
        return _na(name, req, "input carries no scope")
    dst = fx.output.get("scope")
    if not isinstance(dst, dict) or not dst:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"input is scoped {json.dumps(src, sort_keys=True)} but the output emits no scope, "
            "so the output claim is unbounded relative to its input",
            f"CPP-2: without added support, scope must stay equal or become narrower. {COMPLETENESS_ASSUMPTION}",
        )

    src_targets = set(_as_list(src.get("targets")))
    dst_targets = set(_as_list(dst.get("targets")))
    findings: list[str] = []
    verdicts: set[str] = set()

    if src_targets or dst_targets:
        new_targets = sorted(dst_targets - src_targets)
        if not new_targets:
            verdicts.add(NARROWING if dst_targets < src_targets else PRESERVING)
            findings.append(f"target set {sorted(dst_targets)} within input {sorted(src_targets)}")
        else:
            uncovered = [t for t in new_targets if not fx.evidence_covering(t)]
            if uncovered:
                return CheckResult(
                    name,
                    req + ["CPP-1"],
                    VIOLATION,
                    f"output adds targets {new_targets} with no added evidence covering {uncovered}",
                    "CPP-2 with CPP-1: a strengthened dimension must name the added evidence that supports it",
                )
            verdicts.add(STRENGTHENING_SUPPORTED)
            findings.append(f"targets {new_targets} each covered by added evidence")

    src_window, dst_window = src.get("time_window"), dst.get("time_window")
    if src_window is not None and dst_window is not None:
        if src_window == dst_window:
            verdicts.add(PRESERVING)
            findings.append(f"time window unchanged ({src_window})")
        else:
            return CheckResult(
                name,
                req,
                INCONCLUSIVE,
                f"time window changed from {src_window} to {dst_window}; window containment is not "
                "mechanically decidable from opaque window labels",
                "CPP-2",
            )
    elif src_window is not None and dst_window is None:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"input is bounded to window {src_window} but the output emits no time window",
            f"CPP-2. {COMPLETENESS_ASSUMPTION}",
        )

    src_boundary, dst_boundary = src.get("boundary"), dst.get("boundary")
    if src_boundary is not None and dst_boundary is not None:
        if src_boundary == dst_boundary:
            verdicts.add(PRESERVING)
            findings.append("system boundary unchanged")
        else:
            return CheckResult(
                name, req, INCONCLUSIVE, "system boundary changed; containment not mechanically decidable", "CPP-2"
            )
    elif src_boundary is not None and dst_boundary is None:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"input is bounded to {src_boundary!r} but the output emits no system boundary",
            f"CPP-2. {COMPLETENESS_ASSUMPTION}",
        )

    if not verdicts:
        return CheckResult(name, req, NOT_MEASURED, "no comparable scope dimension on both sides", "CPP-2")
    if STRENGTHENING_SUPPORTED in verdicts:
        status = STRENGTHENING_SUPPORTED
    elif NARROWING in verdicts:
        status = NARROWING
    else:
        status = PRESERVING
    return CheckResult(name, req, status, "; ".join(findings), "set containment over represented scope fields")


def check_assurance(fx: Fixture) -> CheckResult:
    name, req = "assurance_independence", ["CPP-10"]
    src, dst = fx.input.get("assurance"), fx.output.get("assurance")
    if src is None or dst is None:
        return _na(name, req, "assurance level not represented on both sides")
    src_rank = ASSURANCE_RANK.get(str(src).upper())
    dst_rank = ASSURANCE_RANK.get(str(dst).upper())
    if src_rank is None or dst_rank is None:
        return CheckResult(name, req, INCONCLUSIVE, f"unknown assurance vocabulary: {src} -> {dst}", "CPP-10")
    if dst_rank > src_rank:
        if fx.evidence_supporting("assurance_independence"):
            return CheckResult(
                name,
                req,
                STRENGTHENING_SUPPORTED,
                f"assurance raised {src} -> {dst} with added evidence naming the independence dimension",
                "CPP-10 with CPP-1",
            )
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"assurance raised {src} -> {dst} without an independently established observer boundary",
            "CPP-10: a claim from the same process or authority domain must not be relabelled independent",
        )
    if dst_rank < src_rank:
        return CheckResult(name, req, NARROWING, f"assurance lowered {src} -> {dst}", "CPP-10")
    return CheckResult(name, req, PRESERVING, f"assurance unchanged ({src})", "CPP-10")


def check_effect_strength(fx: Fixture) -> CheckResult:
    name, req = "effect_strength", ["CPP-9"]
    src_cond = fx.input.get("condition") or {}
    dst_cond = fx.output.get("condition") or {}
    src, dst = src_cond.get("effect_state"), dst_cond.get("effect_state")
    if src is None or dst is None:
        return _na(name, req, "effect state not represented on both sides")
    src_rank, dst_rank = EFFECT_RANK.get(str(src).lower()), EFFECT_RANK.get(str(dst).lower())
    if src_rank is None or dst_rank is None:
        return CheckResult(name, req, INCONCLUSIVE, f"unknown effect vocabulary: {src} -> {dst}", "CPP-9")
    if dst_rank > src_rank:
        if fx.evidence_supporting("effect"):
            return CheckResult(
                name, req, STRENGTHENING_SUPPORTED, f"effect state raised {src} -> {dst} with effect evidence", "CPP-9"
            )
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"effect state raised {src} -> {dst} with no effect evidence",
            "CPP-9: delivery, receipt or acknowledgement must not be upgraded to a target-system effect claim",
        )
    if dst_rank < src_rank:
        return CheckResult(name, req, NARROWING, f"effect state lowered {src} -> {dst}", "CPP-9")
    return CheckResult(name, req, PRESERVING, f"effect state unchanged ({src})", "CPP-9")


def check_basis_pinning(fx: Fixture) -> CheckResult:
    name, req = "basis_pinning", ["CPP-13"]
    def moving_tokens(basis: Any) -> list[str]:
        tokens = re.findall(r"[A-Za-z]+", str(basis).lower())
        return sorted({t for t in tokens if t in MOVING_BASIS_TOKENS})

    src, dst = fx.input.get("basis"), fx.output.get("basis")
    if src is None and dst is None:
        return _na(name, req, "no basis reference represented")

    # Each side is judged on its own. A pinned input does not excuse a moving
    # output: replacing a pinned basis with a moving one is the §7.2 failure mode.
    offenders = [(side, basis, moving_tokens(basis)) for side, basis in (("input", src), ("output", dst)) if basis is not None]
    moving = [(side, basis, tokens) for side, basis, tokens in offenders if tokens]
    if moving:
        detail = "; ".join(
            f"{side} basis {basis!r} is a moving reference ({', '.join(tokens)})" for side, basis, tokens in moving
        )
        if src is not None and dst is not None and not moving_tokens(src) and moving_tokens(dst):
            detail += "; a pinned basis was replaced with a moving one"
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"{detail}, so the exact revision used is not identified",
            "CPP-13: a transformation must identify the exact revision used; a moving URL or 'latest' "
            "reference must not support a frozen reproducibility claim",
        )
    if src is not None and dst is None:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"input names a pinned basis {src!r} but the output emits no basis at all",
            f"CPP-13. {COMPLETENESS_ASSUMPTION}",
        )
    return CheckResult(
        name,
        req,
        PRESERVING,
        "; ".join(f"{side} basis {basis!r} names a pinned revision" for side, basis, _ in offenders),
        "CPP-13",
    )


def check_state_collapse(fx: Fixture) -> CheckResult:
    name, req = "semantic_state_preservation", ["CPP-12"]
    mapping = fx.transformation.get("mapping")
    if not isinstance(mapping, dict) or not mapping:
        return _na(name, req, "no adapter mapping represented")
    collapsed = len(set(map(str, mapping.values()))) < len(mapping)
    if not collapsed:
        return CheckResult(name, req, PRESERVING, "adapter mapping is injective", "mapping arity")
    if fx.transformation.get("preserves_distinctions") is True:
        return CheckResult(
            name,
            req,
            PRESERVING,
            "many-to-one mapping, but the source distinctions are declared reviewable downstream",
            "CPP-12",
        )
    return CheckResult(
        name,
        req,
        VIOLATION,
        f"many-to-one mapping {json.dumps(mapping, sort_keys=True)} with no declared preservation of the lost distinctions",
        "CPP-12: a many-to-one state mapping is non-preserving unless the lost distinctions remain reviewable",
    )


def _shared_numeric_metrics(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    return sorted(
        key
        for key in set(a) & set(b)
        if isinstance(a[key], (int, float))
        and isinstance(b[key], (int, float))
        and not isinstance(a[key], bool)
        and not isinstance(b[key], bool)
    )


def check_perturbation_disclosure(fx: Fixture) -> CheckResult:
    name, req = "perturbation_disclosure", ["CPP-15"]
    if not (fx.baseline and fx.instrumented):
        return _na(name, req, "no baseline/instrumented comparison represented")
    metrics = _shared_numeric_metrics(fx.baseline, fx.instrumented)
    if not metrics:
        return CheckResult(name, req, NOT_MEASURED, "no comparable metric across baseline and instrumented runs", "CPP-15")
    diverging = [m for m in metrics if fx.baseline[m] != fx.instrumented[m]]
    if not diverging:
        return CheckResult(name, req, PRESERVING, f"no divergence on {metrics}", "numeric comparison")
    interference = str(fx.observer_effect.get("execution_interference", "NOT_MEASURED")).upper()
    overhead_measured = fx.instrumented.get("trace_overhead_measured")
    detail = (
        f"instrumented and baseline diverge on {diverging} "
        f"({', '.join(f'{m}: {fx.baseline[m]} -> {fx.instrumented[m]}' for m in diverging)})"
    )
    if overhead_measured is False or interference in ("NOT_MEASURED", "INCONCLUSIVE"):
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"{detail}; the result carries no observer-effect assessment "
            f"(execution_interference={interference}, trace_overhead_measured={overhead_measured})",
            "CPP-15: where observation can alter the measured system, the claim must carry an observer-effect assessment",
        )
    return CheckResult(
        name, req, PRESERVING, f"{detail}; perturbation assessed as {interference}", "CPP-15"
    )


def check_uninstrumented_generalization(fx: Fixture) -> CheckResult:
    name, req = "uninstrumented_generalization", ["CPP-15"]
    declared = str(fx.observer_effect.get("generalizes_to_uninstrumented", "")).upper()
    condition = str((fx.output.get("condition") or {}).get("generalizes_to", "")).lower()
    if not declared and not condition:
        return _na(name, req, "the result does not structurally state what condition it generalizes to")
    interference = str(fx.observer_effect.get("execution_interference", "NOT_MEASURED")).upper()
    generalizes = declared == "YES" or condition in ("uninstrumented", "deployment", "unmonitored")
    if generalizes and interference in ("NOT_MEASURED", "INCONCLUSIVE"):
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"result is generalized beyond the instrumented condition while execution interference is {interference}",
            "CPP-15: with perturbation unmeasured, a claim that the observation represents uninstrumented deployment must not be emitted",
        )
    if declared in ("NOT_MEASURED", "UNKNOWN") and not condition:
        return CheckResult(
            name,
            req,
            NOT_MEASURED,
            f"the result records generalizes_to_uninstrumented={declared} and scopes itself to no condition, "
            "so nothing about generalization was measured",
            "CPP-15",
        )
    return CheckResult(
        name,
        req,
        PRESERVING,
        f"generalization is {declared or condition!r} with execution interference {interference}",
        "CPP-15",
    )


def check_evaluation_awareness(fx: Fixture) -> CheckResult:
    name, req = "evaluation_awareness_transfer", ["CPP-17"]
    if not (fx.evaluation_condition and fx.deployment_condition):
        return _na(name, req, "no evaluation-to-deployment transfer represented")
    aware = fx.evaluation_condition.get("model_knows_monitored")
    if aware is not True:
        return CheckResult(
            name,
            req,
            PRESERVING if aware is False else INCONCLUSIVE,
            f"model_knows_monitored is {aware!r}",
            "CPP-17",
        )
    if fx.evidence_supporting("evaluation_transfer"):
        return CheckResult(
            name,
            req,
            STRENGTHENING_SUPPORTED,
            "evaluation-aware behaviour carried to deployment with added evidence supporting the transfer",
            "CPP-17 with CPP-1",
        )
    return CheckResult(
        name,
        req,
        VIOLATION,
        f"behaviour observed with model_knows_monitored=True is carried to a deployment condition "
        f"({json.dumps(fx.deployment_condition, sort_keys=True)}) with no evidence supporting the transfer",
        "CPP-17: behaviour observed under a detectable evaluation condition must not be generalized to unmonitored deployment",
    )


def check_observation_intervention(fx: Fixture) -> CheckResult:
    """Mechanically enforce CPP-16 for the structured intervention trace.

    Missing or out-of-vocabulary facts never default to preservation. The common
    fixture schema rejects them in the corpus; direct API callers receive an
    undecided result rather than an inferred pass.
    """
    name, req = "observation_intervention_separation", ["CPP-16"]
    trace = fx.observation_intervention
    if not trace:
        return _na(name, req, "no structured observation/intervention trace represented")
    if not isinstance(trace, dict):
        return CheckResult(name, req, INCONCLUSIVE, "intervention trace is not an object", "CPP-16")

    role = str(trace.get("observer_role", "")).upper()
    pre = trace.get("pre_intervention")
    intervention = trace.get("intervention")
    post = trace.get("post_intervention")
    attribution = str(trace.get("output_attribution", "")).upper()
    if role not in {"PASSIVE", "INTERVENING"} or attribution not in {
        "PASSIVE_OBSERVATION",
        "INTERVENED_CONDITION",
    }:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"observer_role={role or '<missing>'}, output_attribution={attribution or '<missing>'}",
            "CPP-16 structured vocabulary",
        )
    if not isinstance(pre, dict) or not pre or not isinstance(post, dict) or not post:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            "pre-intervention or post-intervention state is missing",
            "CPP-16 requires pre-state, intervention, and post-state separation",
        )
    if not isinstance(intervention, dict):
        return CheckResult(name, req, INCONCLUSIVE, "intervention is not an object", "CPP-16")

    applied = intervention.get("applied")
    changes = intervention.get("changes")
    if not isinstance(applied, bool) or not isinstance(changes, list):
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            "intervention.applied or intervention.changes is missing or malformed",
            "CPP-16 structured intervention facts",
        )
    allowed_changes = {"policy", "control_state", "execution_permissions", "model_context"}
    unknown_changes = sorted(
        {str(change) for change in changes if not isinstance(change, str) or change not in allowed_changes}
    )
    if unknown_changes:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"intervention.changes contains unknown values {unknown_changes}",
            "CPP-16 structured intervention vocabulary",
        )
    if applied is False and changes:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"intervention.applied is false but changes are recorded: {sorted(changes)}",
            "CPP-16 structured intervention consistency",
        )
    changed = applied and bool(changes)
    if changed and attribution == "PASSIVE_OBSERVATION":
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"observer changed {sorted(map(str, changes))} but output attribution is PASSIVE_OBSERVATION",
            "CPP-16: effects under observer intervention must not be represented as passively observed facts",
        )
    if role == "PASSIVE" and changed:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"observer_role is PASSIVE while the recorded intervention changed {sorted(map(str, changes))}",
            "CPP-16 observer-role consistency",
        )
    if role == "INTERVENING" and not changed:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            "observer_role is INTERVENING but no applied change is recorded",
            "CPP-16 structured intervention facts",
        )
    if changed and attribution == "INTERVENED_CONDITION":
        return CheckResult(
            name,
            req,
            PRESERVING,
            f"pre-state, changes {sorted(map(str, changes))}, and post-state are separated; output is attributed to the intervened condition",
            "CPP-16 structured intervention trace",
        )
    if role == "PASSIVE" and not changed and attribution == "PASSIVE_OBSERVATION":
        return CheckResult(
            name,
            req,
            PRESERVING,
            "observer is passive, no applied change is recorded, and output is attributed to passive observation",
            "CPP-16 structured intervention trace",
        )
    return CheckResult(
        name,
        req,
        INCONCLUSIVE,
        f"role={role}, applied={applied}, changes={changes}, attribution={attribution}",
        "CPP-16 structured intervention facts",
    )


def check_sampling_accounting(fx: Fixture) -> CheckResult:
    """Mechanically enforce CPP-19 for structured stream-loss accounting."""
    name, req = "sampling_loss_accounting", ["CPP-19"]
    account = fx.sampling_accounting
    if not account:
        return _na(name, req, "no structured sampling/loss accounting represented")
    if not isinstance(account, dict):
        return CheckResult(name, req, INCONCLUSIVE, "sampling account is not an object", "CPP-19")

    observed = account.get("observed_population")
    retained = account.get("retained_population")
    claim = str(account.get("output_population_claim", "")).upper()
    valid_count = lambda value: isinstance(value, int) and not isinstance(value, bool) and value >= 0
    if not valid_count(observed) or not valid_count(retained):
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"observed_population={observed!r}, retained_population={retained!r}",
            "CPP-19 requires explicit non-negative population counts",
        )
    if claim not in {"COMPLETE", "BOUNDED_TO_RETAINED", "UNKNOWN"}:
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"output_population_claim={claim or '<missing>'}",
            "CPP-19 structured completeness vocabulary",
        )
    if retained > observed:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"retained population {retained} exceeds observed population {observed}",
            "CPP-19 population conservation",
        )

    expected_dropped = observed - retained
    dropped = account.get("dropped_population")
    if expected_dropped > 0 and claim == "COMPLETE":
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"retained {retained} of {observed} events but output_population_claim is COMPLETE; "
            f"sampling_rule present={bool(account.get('sampling_rule'))}, loss_metadata present={bool(account.get('loss_metadata'))}",
            "CPP-19: retained evidence must not be reported as a complete population after sampling or loss",
        )
    if expected_dropped > 0:
        exact_loss = valid_count(dropped) and dropped == expected_dropped
        rule_recorded = isinstance(account.get("sampling_rule"), str) and bool(account["sampling_rule"].strip())
        loss_recorded = isinstance(account.get("loss_metadata"), dict) and bool(account["loss_metadata"])
        if claim == "UNKNOWN":
            return CheckResult(
                name,
                req,
                NOT_MEASURED,
                f"retained {retained} of {observed}; output completeness remains UNKNOWN",
                "CPP-19",
            )
        if not (exact_loss and rule_recorded and loss_recorded):
            return CheckResult(
                name,
                req,
                INCONCLUSIVE,
                f"retained {retained} of {observed}; exact_loss={exact_loss}, sampling_rule={rule_recorded}, loss_metadata={loss_recorded}",
                "CPP-19 requires enough sampling/loss metadata to bound the retained evidence",
            )
        return CheckResult(
            name,
            req,
            NARROWING,
            f"retained {retained} of {observed}, recorded {dropped} dropped events, and bounded the output to the retained population",
            "CPP-19 structured sampling and loss account",
        )

    if valid_count(dropped) and dropped != 0:
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"observed and retained populations are both {observed}, but dropped_population is {dropped}",
            "CPP-19 population conservation",
        )
    if claim == "UNKNOWN":
        return CheckResult(name, req, NOT_MEASURED, "population is conserved but completeness is UNKNOWN", "CPP-19")
    return CheckResult(
        name,
        req,
        PRESERVING,
        f"all {observed} observed events were retained and output completeness is {claim}",
        "CPP-19 population conservation",
    )


def check_evidence_resolvability(fx: Fixture) -> CheckResult:
    name, req = "evidence_resolvability", ["CPP-7"]
    items = _evidence_items(fx.input.get("evidence"))
    if not items:
        return _na(name, req, "no structured input evidence represented")
    unverified = [
        item
        for item in items
        if item.get("verified") is False or item.get("resolvable") is False
    ]
    if not unverified:
        return CheckResult(name, req, PRESERVING, "no unresolved or unverified input evidence", "CPP-7")
    dst_assurance = str(fx.output.get("assurance", "")).upper()
    if dst_assurance in ("INDEPENDENT_OBSERVER", "INDEPENDENT_REPLAY"):
        return CheckResult(
            name,
            req,
            VIOLATION,
            f"input evidence {[i.get('ref') for i in unverified]} is unresolved or unverified, "
            f"yet the output asserts assurance {dst_assurance}",
            "CPP-7: an artifact that was not fetched, could not be fetched, was redacted, or was not verified must not be represented as verified",
        )
    if not fx.output.has("assurance"):
        return CheckResult(
            name,
            req,
            INCONCLUSIVE,
            f"input evidence {[i.get('ref') for i in unverified]} is unresolved or unverified and the output "
            "expresses its assurance only in prose; CPP-7 conformance is not mechanically decidable here",
            "CPP-7",
        )
    return CheckResult(name, req, PRESERVING, f"output assurance {dst_assurance} does not assert verification", "CPP-7")


CHECKS: tuple[Callable[[Fixture], CheckResult], ...] = (
    check_status_preservation,
    check_evidence_sink,
    check_denominator,
    check_non_claims,
    check_qualifiers,
    check_scope,
    check_assurance,
    check_effect_strength,
    check_basis_pinning,
    check_state_collapse,
    check_perturbation_disclosure,
    check_uninstrumented_generalization,
    check_evaluation_awareness,
    check_observation_intervention,
    check_sampling_accounting,
    check_evidence_resolvability,
)


# --------------------------------------------------------------------------
# Relation derivation and reconciliation
# --------------------------------------------------------------------------


def derive_relation(results: list[CheckResult]) -> str:
    """Compose per-check outcomes into one relation, always erring toward the
    weaker claim. An undecided check can never be rounded up into a passing
    relation; a violation always dominates."""
    statuses = {r.status for r in results}
    if CHECK_ERROR in statuses:
        return "ERROR"
    if VIOLATION in statuses:
        return "AMPLIFIED_UNSUPPORTED"
    if INCONCLUSIVE in statuses:
        return "INCONCLUSIVE"
    if NOT_MEASURED in statuses:
        return "NOT_MEASURED"
    if STRENGTHENING_SUPPORTED in statuses:
        return "SUPPORTED_STRENGTHENING"
    if NARROWING in statuses:
        return "NARROWER"
    if PRESERVING in statuses:
        return "EQUIVALENT"
    return "NOT_MEASURED"


def reconcile(declared: str, derived: str) -> str:
    if derived in UNDECIDED_RELATIONS:
        return "NOT_MECHANICALLY_DECIDABLE"
    if derived == declared:
        return "AGREES_EXACT"
    if (derived in PASSING_RELATIONS) == (declared in PASSING_RELATIONS):
        return "AGREES_ON_CLASS"
    return "CONTRADICTS"


def evaluate_fixture(fx: Fixture, checks=CHECKS) -> dict[str, Any]:
    results = [check(fx) for check in checks]
    derived = derive_relation(results)
    violations = sorted({req for r in results if r.status == VIOLATION for req in r.requirements})
    evaluated = sorted({req for r in results if r.status != NOT_APPLICABLE for req in r.requirements})
    not_evaluated = sorted(
        {req for r in results if r.status == NOT_APPLICABLE for req in r.requirements} - set(evaluated)
    )
    return {
        "case_id": fx.id,
        "corpus": fx.corpus,
        "name": fx.name,
        "declared_relation": fx.declared_relation,
        "derived_relation": derived,
        "reconciliation": reconcile(fx.declared_relation, derived),
        "derived_violations": violations,
        "declared_violations": fx.declared_violations,
        "declared_violations_not_derived": sorted(set(fx.declared_violations) - set(violations)),
        "derived_is_passing": derived in PASSING_RELATIONS,
        "declared_is_passing": fx.declared_relation in PASSING_RELATIONS,
        "coverage": {"evaluated": evaluated, "not_evaluated": not_evaluated},
        "checks": [r.to_dict() for r in results],
    }


# --------------------------------------------------------------------------
# Corpus validation
# --------------------------------------------------------------------------


def parse_requirements(spec_path: Path) -> list[str]:
    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - surfaced as a run error
        raise RunError(f"cannot read profile text at {spec_path}: {exc}") from exc
    found = re.findall(r"^###\s+(CPP-\d+)\s+—", text, flags=re.MULTILINE)
    if not found:
        raise RunError(f"no CPP requirements parsed from {spec_path}")
    return sorted(set(found), key=lambda r: int(r.split("-")[1]))


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RunError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RunError(f"cannot parse {path}: {exc}") from exc


def validate_corpus(
    fixtures: list[Fixture],
    requirements: list[str],
    schema: dict[str, Any] | None,
    negative_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    problems: list[dict[str, str]] = []

    seen: dict[str, str] = {}
    for fx in fixtures:
        if fx.id in seen:
            problems.append({"kind": "duplicate_id", "case_id": fx.id, "detail": "id appears more than once"})
        seen[fx.id] = fx.corpus
        if fx.declared_relation not in RELATIONS:
            problems.append(
                {"kind": "illegal_relation", "case_id": fx.id, "detail": f"{fx.declared_relation!r} is not a CPP relation"}
            )
        for req in fx.declared_violations:
            if req not in requirements:
                problems.append(
                    {"kind": "unknown_requirement", "case_id": fx.id, "detail": f"{req} is not defined in the profile"}
                )
        is_positive = str(fx.id).startswith("CPP-P")
        if is_positive and fx.declared_relation not in PASSING_RELATIONS:
            problems.append(
                {"kind": "positive_not_passing", "case_id": fx.id, "detail": f"positive fixture declares {fx.declared_relation}"}
            )
        if not is_positive and fx.declared_relation in PASSING_RELATIONS:
            problems.append(
                {"kind": "negative_passing", "case_id": fx.id, "detail": f"negative fixture declares {fx.declared_relation}"}
            )
        if is_positive and fx.declared_violations:
            problems.append(
                {"kind": "positive_with_violations", "case_id": fx.id, "detail": "positive fixture declares violations"}
            )
        if not is_positive and fx.declared_relation == "AMPLIFIED_UNSUPPORTED" and not fx.declared_violations:
            problems.append(
                {"kind": "negative_without_violations", "case_id": fx.id, "detail": "amplification fixture names no requirement"}
            )

    schema_state = "NOT_MEASURED"
    if schema is not None:
        try:
            import jsonschema  # type: ignore
        except ModuleNotFoundError:
            schema_state = "NOT_MEASURED"
        else:
            schema_state = "MEASURED"
            common = jsonschema.Draft202012Validator(schema)
            neg = jsonschema.Draft202012Validator(negative_schema) if negative_schema else None
            for fx in fixtures:
                for error in sorted(common.iter_errors(fx.data), key=lambda e: list(e.path)):
                    problems.append(
                        {
                            "kind": "schema_violation",
                            "case_id": fx.id,
                            "detail": f"fixture.schema.json: {'/'.join(str(p) for p in error.path)}: {error.message}",
                        }
                    )
                if neg is not None and fx.corpus == "negative":
                    for error in sorted(neg.iter_errors(fx.data), key=lambda e: list(e.path)):
                        problems.append(
                            {
                                "kind": "schema_violation",
                                "case_id": fx.id,
                                "detail": f"negative-fixture.schema.json: {'/'.join(str(p) for p in error.path)}: {error.message}",
                            }
                        )

    return {
        "schema_validation_state": schema_state,
        "requirements_defined": requirements,
        "fixture_count": len(fixtures),
        "negative_count": sum(1 for f in fixtures if f.corpus == "negative"),
        "positive_count": sum(1 for f in fixtures if f.corpus == "positive"),
        "problems": sorted(problems, key=lambda p: (p["case_id"] or "", p["kind"], p["detail"])),
        "valid": not problems and schema_state == "MEASURED",
    }


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------


def build_report(conformance_dir: Path, spec_path: Path) -> dict[str, Any]:
    requirements = parse_requirements(spec_path)
    negative = load_json(conformance_dir / "negative-fixtures.json")
    positive = load_json(conformance_dir / "positive-fixtures.json")
    if not isinstance(negative, list) or not isinstance(positive, list):
        raise RunError("fixture corpora must each be a JSON array")

    schema = load_json(conformance_dir / "fixture.schema.json")
    negative_schema = load_json(conformance_dir / "negative-fixture.schema.json")

    fixtures = [Fixture(d, "negative") for d in negative] + [Fixture(d, "positive") for d in positive]
    corpus = validate_corpus(fixtures, requirements, schema, negative_schema)
    evaluations = [evaluate_fixture(fx) for fx in fixtures]

    summary = {
        "relations_derived": {
            rel: sum(1 for e in evaluations if e["derived_relation"] == rel) for rel in RELATIONS
        },
        "reconciliation": {
            key: sum(1 for e in evaluations if e["reconciliation"] == key)
            for key in ("AGREES_EXACT", "AGREES_ON_CLASS", "NOT_MECHANICALLY_DECIDABLE", "CONTRADICTS")
        },
        "mechanically_decided": sum(1 for e in evaluations if e["derived_relation"] not in UNDECIDED_RELATIONS),
        "not_mechanically_decidable": sorted(
            e["case_id"] for e in evaluations if e["derived_relation"] in UNDECIDED_RELATIONS
        ),
        "contradictions": sorted(e["case_id"] for e in evaluations if e["reconciliation"] == "CONTRADICTS"),
    }

    return {
        "cpp_version": CPP_VERSION,
        "validator": {
            "name": "cpp-reference-validator",
            "version": VALIDATOR_VERSION,
            "semantic_entailment": "NOT_IMPLEMENTED",
            "note": (
                "This validator decides only what the structured fixture fields decide. "
                "Natural-language semantic entailment is not implemented and is never guessed; "
                "affected checks report NOT_MEASURED or INCONCLUSIVE."
            ),
            "modelling_assumption": COMPLETENESS_ASSUMPTION,
            "exit_code_meaning": "run and corpus validity only; claim verdicts are in this report body",
        },
        "corpus_validation": corpus,
        "summary": summary,
        "evaluations": evaluations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CPP v0.1 reference conformance validator")
    parser.add_argument("--conformance-dir", type=Path, default=DEFAULT_CONFORMANCE)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--report", type=Path, default=None, help="write the JSON report to this path")
    parser.add_argument("--quiet", action="store_true", help="suppress the human-readable summary on stderr")
    parser.add_argument(
        "--fail-on-contradiction",
        action="store_true",
        help="policy gate: exit 4 if a declared relation contradicts the derived relation",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(args.conformance_dir, args.spec)
    except RunError as exc:
        print(f"run error: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    corpus = report["corpus_validation"]
    summary = report["summary"]
    if not args.quiet:
        print(
            f"corpus: {corpus['negative_count']} negative, {corpus['positive_count']} positive; "
            f"schema validation {corpus['schema_validation_state']}; problems {len(corpus['problems'])}",
            file=sys.stderr,
        )
        print(
            f"relations: decided {summary['mechanically_decided']}/{corpus['fixture_count']}; "
            f"agree {summary['reconciliation']['AGREES_EXACT'] + summary['reconciliation']['AGREES_ON_CLASS']}; "
            f"undecidable {summary['reconciliation']['NOT_MECHANICALLY_DECIDABLE']}; "
            f"contradictions {summary['reconciliation']['CONTRADICTS']}",
            file=sys.stderr,
        )

    if corpus["schema_validation_state"] != "MEASURED":
        print(
            "run incomplete: JSON Schema validation could not be executed (install `jsonschema`). "
            "This is not a passing result.",
            file=sys.stderr,
        )
        return 5
    if corpus["problems"]:
        return 3
    if args.fail_on_contradiction and summary["contradictions"]:
        return 4
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
