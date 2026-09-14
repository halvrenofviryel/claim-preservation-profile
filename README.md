# Claim Preservation Profile

**CPP v0.1 — Experimental.** An experimental specification and conformance corpus
for preserving evidence-backed claim scope, qualifications, non-claims, assurance
state, and observer validity across AI assurance pipelines.

Author proposal. Not a standard, not adopted by any standards body, not part of
AIREP, Measurement Axioms, CDE-12 or draft-abak, not independently reviewed, not
independently reproduced, not deployed. See [STATUS.md](STATUS.md).

## The problem

An AI assurance pipeline moves the same underlying evidence through many hands:
`producer → verifier → adapter → normalizer → aggregator → dashboard → report → decision-maker`.
Each stage is written by someone solving a local problem — fit this into our schema,
make the summary fit the slide, drop the fields nobody reads — and each stage is
syntactically valid on its own terms. Yet the claim that arrives at the
decision-maker can be substantially stronger than the evidence that left the
producer: a bounded observation has become a universal statement, a `NOT_MEASURED`
has vanished from an aggregate, an acknowledgement has become an effect. No stage
lied. The claim boundary simply was not part of the payload, so nothing carried it.

The problem CPP addresses is therefore **not** whether evidence exists, and not
whether it can be fetched or checked. It is whether **evidence-backed claim
boundaries survive verification, normalization, aggregation, adaptation,
dashboarding, reporting, and publication without silent semantic amplification.**

## The central invariant

> A transformation MUST NOT increase the semantic strength, scope, certainty,
> causal implication, independence claim, completeness claim, or assurance level of
> an evidence-backed claim unless identifiable additional evidence is introduced and
> is sufficient for that increase.

Two consequences follow, and both are deliberate.

Claim strength is **a partial order over independent dimensions**, not a score.
There is no single "claim strength" number in CPP, because a transformation that
narrows the population while strengthening the causal claim is not stronger or
weaker — it is `INCOMPARABLE`, and flattening it to a number is precisely the
failure mode the profile is about.

Not knowing is **a state, not a gap**. `NOT_MEASURED`, `INCONCLUSIVE` and `ERROR`
are outcomes that must survive to the reader intact. They may never be absorbed
into a pass.

## Why it exists

Assurance work has largely solved the problem of getting evidence to exist and be
checkable — signatures, transparency logs, provenance, attestation, tracing. That
machinery establishes things about *records*. The gap CPP addresses opens
afterwards: between a verified record and the sentence a human or a system acts on.
A valid signature establishes that a record is intact; it establishes nothing about
whether the recorded event occurred. An acknowledgement establishes receipt; it
establishes nothing about effect. An instrumented evaluation establishes behaviour
under instrumentation; it establishes nothing about the uninstrumented system unless
the perturbation was bounded. Each of these distinctions is understood in isolation.
What is missing is an obligation that they **travel**, as data, through every
downstream transformation — which is what this profile proposes.

## What is in this repository

| Path | Contents |
| --- | --- |
| [`spec/v0.1/CLAIM_PRESERVATION_PROFILE.md`](spec/v0.1/CLAIM_PRESERVATION_PROFILE.md) | The profile: claim model, relation vocabulary, twenty normative requirements (CPP-1 … CPP-20), observer/probe-effect extension. |
| [`spec/v0.1/claim-preservation-result.schema.json`](spec/v0.1/claim-preservation-result.schema.json) | Machine-readable result schema. Keeps dimensions separate; blocks passing relations that carry violations. |
| [`spec/v0.1/CHECKSUMS.sha256`](spec/v0.1/CHECKSUMS.sha256) | v0.1.0 integrity manifest for the two normative files above. |
| [`conformance/negative-fixtures.json`](conformance/negative-fixtures.json) | The original 20 negative cases plus two hardening cases for CPP-16 and CPP-19. Four loose requirement attributions in the original set are corrected without changing their expected relations. |
| [`conformance/positive-fixtures.json`](conformance/positive-fixtures.json) | 15 positive controls. Thirteen are paired with a negative case and name the fact the pairing turns on; the validator separates ten of those pairs mechanically, and the other three say plainly that it cannot. |
| [`conformance/fixture.schema.json`](conformance/fixture.schema.json) | Common fixture schema, with backwards-compatible aliases for the seed corpus's field names. |
| [`conformance/negative-fixture.schema.json`](conformance/negative-fixture.schema.json) | The original seed schema, kept so the seed corpus keeps validating against what it was written for. |
| [`conformance/validate.py`](conformance/validate.py) | Reference validator. Offline, deterministic, no semantic guessing. |
| [`tests/`](tests) | Conformance tests, including mutation tests over load-bearing validator rules. |
| [`research/PRIOR_ART_AND_SCOPE.md`](research/PRIOR_ART_AND_SCOPE.md) | What CPP does not claim to invent, and the bounded contribution it does claim. |
| [`research/CROSS_PROJECT_CONSISTENCY_AUDIT.md`](research/CROSS_PROJECT_CONSISTENCY_AUDIT.md) | Pinned-source audit of every CPP characterization of AIREP, Measurement Axioms, CDE-12, and draft-abak. |

## A worked example of unsupported amplification

```text
Evidence:
"Control C was acknowledged at enforcement point EP-A."

Bad downstream claim:
"Safeguard C prevented the unsafe action."

Result:
AMPLIFIED_UNSUPPORTED
```

Three separate increases happened in one sentence, and none of them acquired new
evidence. The **execution/effect** dimension moved from `acknowledged` to an
observed effect (CPP-9). The **causal** dimension moved from co-occurrence to
prevention (CPP-1). The **population scope** silently dropped `EP-A`, so a claim
about one enforcement point now reads as a claim about the system (CPP-2).

The claim-preserving version of the same evidence is not a weaker-sounding hedge;
it is a different, accurate sentence with its boundary attached:

```text
"Control C was acknowledged at EP-A during window T1.
 Does not establish that C was applied.
 Does not establish that C prevented any action."
```

## Relation vocabulary

Every evaluator classifies the relation between an input claim and an output claim
as exactly one of:

| Relation | Meaning | Passing? |
| --- | --- | --- |
| `EQUIVALENT` | Same supported semantics. | yes |
| `NARROWER` | Output is strictly weaker or more scoped. | yes |
| `SUPPORTED_STRENGTHENING` | Output is stronger, and identifiable added evidence supports the increase. | yes |
| `AMPLIFIED_UNSUPPORTED` | Output is stronger without sufficient added evidence. | no |
| `INCOMPARABLE` | Some dimensions narrow while others strengthen; no safe order. | no |
| `NOT_MEASURED` | The relation was not evaluated. | no |
| `INCONCLUSIVE` | Evaluated, but the available information does not decide it. | no |
| `ERROR` | The evaluation failed technically. | no |

The last three are the ones that get quietly lost in real pipelines, so the profile
states the rule directly: they may not be collapsed into `EQUIVALENT`, `NARROWER`,
or any other passing state.

## Observer validity and the probe effect

Measuring an AI system changes it, and the change is not always small. CPP keeps
this in v0.1 rather than deferring it, and separates two channels that are usually
conflated.

**Runtime perturbation** — observation changes the execution itself: latency,
CPU and memory, scheduling and race outcomes, timeout behaviour, buffering and I/O,
network calls, prompts and context, tool availability, permissions, control flow,
and the model's own awareness that it is being evaluated.

**Semantic perturbation** — the evidence pipeline changes what the claim means:
dropped qualifiers, deleted non-claims, denominator loss, state collapse, self-report
becoming "verified", bounded evidence becoming a universal statement, integrity
becoming truth, acknowledgement becoming effect.

The requirements that follow from this are CPP-15 through CPP-19: disclose the
observer effect, separate observation from intervention, qualify anything the
evaluated model could tell was an evaluation, treat evidence-sink failure as a
measurement failure, and account for sampling and loss.

**This is not quantum mechanics.** CPP is not derived from and does not depend on
the Heisenberg uncertainty principle; any resemblance is at most a loose analogy.
The perturbation here is entirely classical: instrumentation costs resources and
changes timing, and observed systems can behave differently when they can tell they
are observed.

## Relationship to existing Phionyx work

CPP draws on ideas explored elsewhere in the Phionyx research program. It does not
alter any of them and is not a component of any of them.

**AIREP v0.1/v0.2** provide explicit scope and `does_not_cover`; v0.1 also defines
evidence-reference resolvability and an integrity-not-truth boundary, while v0.2
adds stage-specific artifact families and references. CPP is not an AIREP profile
and does not change AIREP conformance.

**Measurement Axioms v1.0** keeps `NOT_MEASURED`, `INCONCLUSIVE`, and `ERROR`
distinct from positive outcomes and separates measurement, decision, execution,
enforcement, and evidence states. Its frozen v1.0 text does not define CPP's
observer-validity/probe-effect model. CPP does not modify it. The reference
validator follows the narrower shared principle that a valid run and a positive
measurement are different facts.

**CDE-12 v0.2** is a record-focused measurement instrument: it bounds what a reader
can establish, records evidence tiers, distinguishes `not tested` from `not
demonstrated`, and separates delivery, enforcement, effect, authority, and bounded
negative records in C8–C12. CPP asks whether such bounded conclusions remain
bounded downstream; it does not modify CDE-12.

The published individual Internet-Draft **draft-abak-01** proposes separate
structural and claim-support results, scope/non-claim qualification, delivery/effect
separation, and intermediary semantic preservation. CPP applies a similar
preservation question to broader AI assurance transformations. **CPP is not IETF
work; this reference implies no IETF or working-group review, adoption, consensus,
or endorsement.**

The exact source commits and statement-by-statement classifications are in
[`research/CROSS_PROJECT_CONSISTENCY_AUDIT.md`](research/CROSS_PROJECT_CONSISTENCY_AUDIT.md).

The position paper *Access Is Not Yet Verifiability: Toward a Claim-Preserving
Evidence Contract for AI Assurance* is the conceptual motivation for this work. It
is a position paper, not normative specification text; where the two differ, the
profile in `spec/v0.1/` governs this repository.

## Status and explicit non-claims

CPP v0.1 is an **experimental author proposal**. [STATUS.md](STATUS.md) carries the
machine-readable status block. In particular, CPP does **not** claim:

- to be an industry standard, an IETF standard, or an adopted standard of any kind;
- to be part of AIREP, Measurement Axioms, CDE-12, or draft-abak;
- to have been independently reviewed, reproduced, validated, or deployed;
- to be consensus-backed;
- that the underlying evidence is true merely because its claim was preserved;
- that observer effects can always be eliminated;
- that one scalar assurance score can safely summarize all claim dimensions;
- that an instrumented evaluation predicts uninstrumented deployment;
- that cryptographic integrity establishes semantic correctness;
- that provenance establishes causality;
- to have solved natural-language semantic entailment. The reference validator
  decides only what the structured fields decide, and reports `NOT_MEASURED` or
  `INCONCLUSIVE` everywhere else. Six of the twenty-two negative cases are undecidable
  by it, and it says so.

The conformance fixtures are author-created research artifacts, not independent
empirical validation.

The corpus now exercises **CPP-16** (observation/intervention separation) and
**CPP-19** (sampling and loss accounting) with structured negative/positive
near-neighbour pairs and load-bearing validator checks. This demonstrates internal
mechanical discrimination only, not independent validation or deployment fitness.
Four loose requirement attributions in the original negative set are corrected in
the v0.1.0 release; the expected relation of every case remains unchanged. The
correction record is in
[`research/PRIOR_ART_AND_SCOPE.md`](research/PRIOR_ART_AND_SCOPE.md#6-corrections-to-original-negative-fixture-attributions).

## Verification

```bash
# 1. dependencies (JSON Schema validation is the one external dependency)
python3 -m pip install -e '.[dev]'

# 2. integrity of the v0.1.0 normative artifacts
( cd spec/v0.1 && sha256sum -c CHECKSUMS.sha256 )

# 3. validator over the whole corpus, report to stdout
python3 conformance/validate.py

# 4. test suite
python3 -m pytest tests -q
```

The validator's exit code reports **run validity and corpus validity only**:

| Exit | Meaning |
| --- | --- |
| 0 | Run completed and the corpus is structurally valid. |
| 2 | Run could not be performed (bad arguments, unreadable or unparseable input). |
| 3 | Run completed but the corpus is structurally invalid. |
| 4 | Policy gate: `--fail-on-contradiction` was given and a declared relation contradicts the derived relation. |
| 5 | Run incomplete: a required check could not be executed (for example, `jsonschema` is not installed). |

Exit 0 does **not** mean every claim was preserved. It means the run was valid.
Claim verdicts are in the report body, per fixture, with the requirements each
check examined and the requirements it did not.

## Citation

See [CITATION.cff](CITATION.cff).

> Abak, A. T. (2026). *Claim Preservation Profile*, version 0.1. Phionyx.

## License

Specification, documentation and fixtures: **CC BY 4.0** ([LICENSE](LICENSE)).
Validator and tests: **Apache-2.0** ([LICENSE-CODE](LICENSE-CODE)).
The boundary is stated in [LICENSE](LICENSE#dual-licensing-boundary).
