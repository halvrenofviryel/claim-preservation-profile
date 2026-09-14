# Prior art and scope

This document exists to keep the repository's novelty claims narrow. Where two
readings are defensible, the narrower one is recorded here.

## 1. What CPP does not claim to invent

CPP v0.1 makes **no claim of invention, priority, or originality** over any of the
following. All of them are established, most of them by decades of work, and CPP
builds on them rather than replacing them:

- **Claim/evidence relationships.** The idea that a claim is supported by evidence,
  and that the support can be examined, is foundational to argumentation, to
  scientific reporting, and to safety engineering.
- **Assurance cases.** Structured argument connecting claims, arguments and
  evidence — including the goal-structuring tradition and its many notations — long
  predates this work.
- **Evidence contracts** as a generic term. The phrase is in general use for
  agreements about what evidence a party will supply and in what form.
- **"Claim-preserving"** as an English or technical phrase. It is an ordinary
  compound and appears in many fields, including formal methods and logic, where
  preservation of a property under transformation is a standard notion.
- **Multi-valued evaluation outcomes.** Test and verification frameworks have long
  distinguished pass, fail, error, skipped, inconclusive and not-run. CPP adopts
  this rather than inventing it.
- **Signed evidence, transparency logs, attestation.** Cryptographic integrity and
  verifiable records are mature engineering.
- **Provenance.** Tracking where data came from and how it was derived is an
  established field with its own standards and models.
- **Tracing and probe-effect research.** That instrumentation perturbs the system it
  measures is a long-standing result in performance analysis, distributed tracing,
  profiling and debugging, with a substantial literature on probe effect and
  observer overhead.
- **The observation that access is not assurance.** That being able to fetch or read
  a record does not establish that the record is true, complete, or sufficient, is
  not a new observation.
- **The observation that instrumentation can perturb execution.** Likewise
  established.

Two further points belong in this list because they are easy to mistake for CPP's
contribution:

- **Evaluation awareness in AI systems** — that a model may behave differently when
  it can tell it is being evaluated — is an actively studied problem in AI
  evaluation, not something CPP discovered.
- **Semantic drift in reporting and aggregation** is a familiar complaint in
  metrics, statistics and governance reporting. Denominator loss and state collapse
  are recognised failure modes.

## 2. Candidate contribution

The bounded contribution CPP claims is this:

> CPP treats preservation of evidence-backed claim scope, qualifications,
> non-claims, assurance state, and observer-validity limitations as an **end-to-end
> interoperability obligation across AI assurance transformations.**

The load-bearing words are *end-to-end*, *interoperability obligation*, and
*across transformations*. The individual distinctions CPP protects — integrity is
not truth, acknowledgement is not effect, self-report is not independence, an
instrumented measurement is not an uninstrumented one, `NOT_MEASURED` is not a pass
— are each well understood in their own domain. What CPP proposes is that they are
made into transferable obligations on every intermediary in the chain, expressed in
machine-readable form, and checkable as a conformance property of the pipeline
rather than as a matter of good drafting at the final report.

Whether that framing is itself novel is not settled here. It is a candidate
contribution, offered for review.

### Priority distinctions

| Question | CPP's claim |
| --- | --- |
| Exact-phrase priority | Not established. Section 3 records only a bounded search observation. |
| Concept priority | Not claimed. The component concepts and failure modes have extensive prior art. |
| Combination novelty | A candidate contribution, not an established novelty finding. |
| Established prior art | The concepts listed in section 1 are treated as prior art and are not claimed as inventions. |

## 3. Search observation on one phrase

> No earlier indexed public use has yet been identified by the authors for the exact
> phrase **"claim-preserving evidence contract"**.

This is a **bounded search observation, not a claim of universal priority.** It
records only what a search by the authors did not surface. It does not establish
that the phrase is unused, that the underlying idea is unprecedented, or that no
equivalent construction exists under different wording. Search coverage is partial
by nature: indexed sources are a subset of published sources, published sources are
a subset of the field's working vocabulary, and equivalent ideas routinely travel
under different names across communities that do not cite each other.

Nothing in this repository should be read as "first", "invented", "original", or
"novel" on the strength of this observation.

## 4. Formal novelty remains open

Formal novelty is **not established** and remains open to further literature review.
The search underlying this repository has not been systematic. In particular, the
following areas have not been reviewed to the depth that a novelty claim would
require, and any one of them could contain prior work that anticipates part or all
of CPP's framing:

- safety and security assurance-case literature, including confidence arguments and
  assurance-case defeaters;
- provenance and workflow-provenance models, and their treatment of derivation
  semantics;
- semantic-web and knowledge-representation work on claim attribution, nanopublications,
  and scope-restricted assertions;
- database and stream-processing work on aggregation semantics, null handling,
  and the preservation of unknown values;
- measurement science and metrology on uncertainty propagation and the reporting of
  measurement conditions;
- clinical-trial and systematic-review reporting standards, which have addressed
  scope creep, selective reporting and denominator integrity in depth;
- statistical disclosure control, on how redaction interacts with what remains
  inferable;
- formal-methods literature on property-preserving refinement and abstraction, which
  is the closest formal analogue to the partial order CPP describes;
- AI evaluation literature on construct validity, evaluation gaming and
  monitoring-aware behaviour.

Anyone identifying prior work in these areas that anticipates CPP's framing is
invited to say so; the appropriate response is to narrow the contribution claim in
section 2, not to broaden the repository's language.

## 5. Scope boundaries of CPP v0.1

**In scope.** The semantics of claim transformation between stages of an AI
assurance pipeline; what a transformed claim may assert relative to its input and
any added evidence; how non-success and unknown states must survive; how observer
and probe effects constrain what a measurement can support.

**Out of scope.** Whether the underlying AI system is safe, correct, aligned or
compliant. Whether the original evidence is true. How evidence is produced, signed,
stored or transported. What a given organisation should decide once a preserved
claim reaches it. Natural-language semantic entailment in the general case — the
reference validator explicitly does not attempt it, and reports `NOT_MEASURED` or
`INCONCLUSIVE` rather than guessing.

**Relationship boundaries.** CPP v0.1 does not modify AIREP, Measurement Axioms
v1.0, CDE-12, or the draft-abak IETF work area, is not a component or profile of any
of them, and carries no implication of IETF or working-group review, adoption,
consensus, or endorsement. The specific source-supported relationships and their
limits are recorded in [`CROSS_PROJECT_CONSISTENCY_AUDIT.md`](CROSS_PROJECT_CONSISTENCY_AUDIT.md).

## 6. Corrections to original negative-fixture attributions

The public baseline preserved the original twenty negative fixtures byte-for-byte.
The v0.1.0 release corrects four loose requirement attributions in place while
leaving every fixture's *expected relation* unchanged. The baseline remains intact
on `main` and in commit `e5961ab2c54a2ade57bd2901131006480ed7b750`.

- **CPP-N02 → CPP-13.** The fixture's data is `input_scope: {"time_window": "T1"}`
  and an output claiming current health. CPP-13 is about identifying the exact
  evidence, specification, model or policy revision used, and about a moving basis
  not supporting a frozen reproducibility claim. The fixture carries no basis, no
  revision and no reproducibility claim. The defect it actually shows is temporal
  scope broadening, which its other two identifiers (CPP-1, CPP-2) already cover.
- **CPP-N16 → CPP-6.** The fixture supplies only a moving `input_basis`. CPP-6
  requires retained links to input claims, transformation rule and version,
  transformer identity, and evidence references. Nothing in the fixture shows such a
  link being dropped: a moving URL is a link that is retained but unpinned, which is
  CPP-13 and nothing further.
- **CPP-N18 → CPP-20.** CPP-20 is scoped to a transformed *assurance result* being
  displayed or exported, and to a bare `PASS` or `VERIFIED` shown without its claim
  boundary. N18's output is a timeout-rate figure, not an assurance verdict. CPP-15,
  which the fixture also names, is the requirement the data supports.
- **CPP-N06 → CPP-20.** Borderline rather than wrong. The output is
  `"Delivery confirmed at EP-A."`, not a bare `PASS`, so the second clause of CPP-20
  does not apply; the first clause arguably does. CPP-4, also named, is the primary
  and sufficient attribution.

The corrections are: N02 removes CPP-13 and retains CPP-1/CPP-2; N06 removes CPP-20
and retains CPP-4; N16 removes CPP-6 and retains CPP-13; N18 removes CPP-20 and
retains CPP-15. Tests pin these exact attributions and the unchanged
`AMPLIFIED_UNSUPPORTED` relations.

CPP-16 and CPP-19 are now exercised by structured negative/positive near-neighbour
pairs (`CPP-N21`/`CPP-P14` and `CPP-N22`/`CPP-P15`) and corresponding validator
checks. Mutation tests establish that removing either new rule loses its negative
detection. This is internal mechanical evidence, not independent validation.

## 7. Provenance of this repository's artifacts

The profile text and the original twenty negative fixtures came from a v0.1 seed
bundle supplied by the author. Their exact public baseline bytes remain available
at commit `e5961ab2c54a2ade57bd2901131006480ed7b750`. Five
explicit, substantive corrections were made to the profile text and every one of
them is listed in [`../CHANGELOG.md`](../CHANGELOG.md). Everything else in this
repository — the result schema, the common fixture schema, the positive controls,
the validator, the tests, and these documents — was written for this repository and
is author-created research material, not independent validation.
