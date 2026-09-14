# Claim Preservation Profile (CPP) v0.1

**Version:** 0.1  
**Status:** Experimental technical profile  
**Normative status:** Author proposal. Not a standard, not adopted, not independently reviewed, not independently reproduced.  
**Purpose:** Define a machine-checkable contract for preserving the semantic strength, scope, qualifications, non-claims, and provenance of evidence-backed claims as they pass through AI assurance pipelines.

## 1. Problem statement

AI assurance pipelines often transform the same underlying evidence through several stages:

`producer → verifier → adapter → normalizer → aggregator → dashboard → report → decision-maker`

A downstream representation can silently become stronger than the evidence supports even when every individual transformation is syntactically valid. Examples include:

- a bounded observation becoming a universal statement;
- `NOT_MEASURED` disappearing from an aggregate;
- a receiver acknowledgement becoming a claim of successful effect;
- an integrity-checked record becoming a claim that the recorded fact is true;
- a self-report becoming "independently verified";
- an instrumented evaluation result being generalized to uninstrumented deployment.

CPP treats these as **claim-preservation failures**, not merely presentation errors.

## 2. Design principle

A transformation MUST NOT increase the semantic strength, scope, certainty, causal implication, independence claim, completeness claim, or assurance level of an evidence-backed claim unless identifiable additional evidence is introduced and is sufficient for that increase.

CPP does not require one scalar "claim strength" score. Claim strength is a **partial order over independent dimensions**. A transformation that narrows one dimension but strengthens another is `INCOMPARABLE` unless the strengthening is explicitly justified.

## 3. Core model

A claim is modeled as:

`C = (P, S, Q, N, E, A, V)`

where:

- `P` — proposition: what is asserted;
- `S` — scope: population, time window, system boundary, target set, operation set;
- `Q` — qualifiers: conditions, uncertainty, caveats, applicability limits;
- `N` — non-claims: explicit statements of what is *not* established;
- `E` — evidence references and provenance;
- `A` — assurance attributes: producer-asserted, integrity-checked, key-attributed, independently verified, replayed, etc.;
- `V` — observation validity metadata, including possible observer/probe effects.

A transformation is:

`T(C_in, E_added) -> C_out`

A transformation is claim-preserving only when the output is supported by the union of inherited evidence and explicitly added evidence, and every strengthening is attributable to that added support.

## 4. Claim-relation vocabulary

A compliant evaluator MUST classify the relation between an input and output claim as one of:

- `EQUIVALENT` — same supported semantics;
- `NARROWER` — output is strictly weaker or more scoped;
- `SUPPORTED_STRENGTHENING` — output is stronger, but the added evidence explicitly supports the strengthening;
- `AMPLIFIED_UNSUPPORTED` — output is stronger without sufficient added evidence;
- `INCOMPARABLE` — some dimensions narrow while others strengthen, or no safe order can be established;
- `NOT_MEASURED` — the relation was not evaluated;
- `INCONCLUSIVE` — the relation was evaluated but available information does not decide it;
- `ERROR` — the relation evaluation failed technically.

`NOT_MEASURED`, `INCONCLUSIVE`, and `ERROR` MUST NOT be collapsed to `EQUIVALENT`, `NARROWER`, or any passing state.

## 5. Strength dimensions

A profile implementation SHOULD evaluate at least these dimensions independently:

1. **Population scope** — subset / equal / superset / unknown.
2. **Temporal scope** — shorter / equal / longer / unknown.
3. **Boundary scope** — narrower / equal / broader / unknown.
4. **Quantifier strength** — e.g. `some < most < all`.
5. **Epistemic modality** — e.g. `reported < observed < supported < independently verified`; exact vocabulary is profile-defined.
6. **Causal strength** — e.g. `co-occurred < associated < contributed < caused`; exact vocabulary is profile-defined.
7. **Assurance independence** — self-asserted / same-process checked / independent observer / independent replay.
8. **Completeness claim** — sampled / bounded-complete / globally complete / unknown.
9. **Freshness/currentness** — historical / valid-at-T / current / unknown.
10. **Execution/effect strength** — issued / received / acknowledged / applied / independently observed effect.

No total ordering across all dimensions is assumed.

## 6. Normative requirements

### CPP-1 — No silent strengthening
A transformer MUST NOT emit a stronger claim unless it records the dimension strengthened, the added evidence, and the rule by which that evidence supports the increase.

### CPP-2 — Scope monotonicity
Without added support, population, temporal, boundary, and target scope MUST stay equal or become narrower.

### CPP-3 — Qualifier preservation
Qualifiers relevant to the output claim MUST be preserved unless each removed qualifier is explicitly discharged by added evidence.

### CPP-4 — Non-claim preservation
A non-claim relevant to the output scope MUST remain visible unless it is explicitly discharged by added evidence. Absence of a non-claim field MUST NOT be interpreted as discharge.

### CPP-5 — Unknown/non-success preservation
`NOT_MEASURED`, `INCONCLUSIVE`, `ERROR`, withheld states, missing evidence, and unresolved references MUST remain distinguishable downstream.

### CPP-6 — Provenance continuity
Every transformed claim MUST retain links to the input claim(s), transformation rule/version, transformer identity, and inherited/additional evidence references.

### CPP-7 — Evidence resolvability honesty
A referenced artifact that was not fetched, could not be fetched, was redacted, or was not verified MUST NOT be represented as verified.

### CPP-8 — Integrity is not truth
Hash validity, signature validity, canonicalization, transparency-log inclusion, or chain integrity MUST NOT by themselves upgrade a claim from "record integrity established" to "recorded fact established."

### CPP-9 — Observation is not effect
Delivery, receipt, acknowledgement, acceptance, or enforcement-state evidence MUST NOT be upgraded to a target-system effect claim without effect evidence.

### CPP-10 — Self-report is not independence
A claim produced by the governed system, the same process, or a component under the same failure/authority domain MUST NOT be relabeled "independently observed" without an independently established observer boundary.

### CPP-11 — Aggregation preserves denominators
Aggregation MUST preserve the assessed population, excluded population, unmeasured population, and denominator construction. Dropped/errored/withheld cases MUST NOT silently disappear from the denominator.

### CPP-12 — Semantic-state preservation across adapters
Adapters and normalizers MUST preserve governance-relevant distinctions. A many-to-one mapping such as `DENY | DEFER | TIMEOUT | UNRESOLVED -> FAILED` is non-preserving unless the lost distinctions remain reviewable and the output claim is qualified accordingly.

### CPP-13 — Mutable-basis disclosure
A transformation MUST identify the exact evidence/specification/model/policy revision used. A moving URL or `latest` reference MUST NOT support a frozen reproducibility claim.

### CPP-14 — Redaction must not strengthen
Redaction, summarization, truncation, compression, or privacy filtering MUST NOT remove limitations in a way that makes the surviving claim stronger.

### CPP-15 — Observer-effect disclosure
If measurement, evaluation, tracing, logging, prompting, instrumentation, or recording can alter the measured system or its execution conditions, the claim MUST carry an observer-effect assessment.

At minimum:

- whether the subject can detect that it is under evaluation/observation;
- whether observation changes latency, scheduling, resource use, control flow, context, prompts, tools, permissions, or state;
- whether evidence recording is in the critical path;
- whether an uninstrumented or lower-intrusion comparator exists;
- whether perturbation was `MEASURED`, `BOUNDED`, `NOT_MEASURED`, or `INCONCLUSIVE`.

### CPP-16 — Observation/intervention separation
A component that both observes and changes policy, control state, execution permissions, or model context is an **intervention**, not a passive observer. Its records MUST distinguish observed facts from effects caused by the observer itself.

### CPP-17 — Evaluation-awareness qualification
If the evaluated AI can infer that it is in an evaluation/monitoring condition, behavior observed under that condition MUST NOT be generalized to unmonitored deployment without explicit evidence supporting that transfer.

### CPP-18 — Evidence-sink failure is a measurement failure
If the evidence sink, exporter, logger, verifier, or recorder fails, the pipeline MUST emit a distinguishable non-success state where possible. Silent recording failure MUST NOT produce a positive assurance result.

### CPP-19 — Sampling/loss accounting
Sampling, dropped spans, filtered events, backpressure loss, queue overflow, or selective retention MUST be recorded with enough metadata to bound what the retained evidence can establish.

### CPP-20 — Claim-preservation result co-exposure
Where a transformed assurance result is displayed or exported, the preservation result and material qualifications MUST be exposed in the same result context. A bare `PASS` or `VERIFIED` without its claim boundary is non-conformant.

## 7. Observer/probe-effect extension

CPP uses **observer effect** in the computer-systems sense, not as a statement of quantum mechanics.

CPP is not derived from, and does not depend on, the Heisenberg uncertainty principle or any other result of quantum mechanics. Any resemblance is at most a loose analogy. The perturbation CPP models is classical: instrumentation consumes resources, changes timing and control flow, and can be visible to the observed system; and evidence pipelines change what records mean. Both are ordinary software and measurement-semantics problems.

Two distinct perturbation channels are modeled:

### 7.1 Runtime perturbation
The observer changes the system being measured, for example by:
- increasing latency or CPU/memory use;
- changing scheduling or race outcomes;
- changing timeout behavior;
- adding I/O, locks, buffering, serialization, or network calls;
- altering prompt/context/tool state;
- changing control flow or permissions;
- making evaluation status visible to the model.

### 7.2 Semantic perturbation
The evidence pipeline changes what the evidence *means*, for example by:
- collapsing distinct states;
- dropping qualifiers/non-claims;
- changing denominators;
- converting self-report to "verified";
- summarizing bounded evidence into a universal statement;
- replacing a pinned basis with a mutable "latest" basis.

Both must be controlled.

## 8. Observer-effect fields

A CPP record SHOULD expose:

```yaml
observer_effect:
  subject_awareness:        YES | NO | UNKNOWN | NOT_MEASURED
  execution_interference:   NONE_OBSERVED | MEASURED | BOUNDED | INCONCLUSIVE | NOT_MEASURED
  critical_path:            true | false | unknown
  evidence_write_in_path:   true | false | unknown
  comparator:
    kind:                   NONE | UNINSTRUMENTED | LOWER_INTRUSION | SHADOW | REPLAY
    reference:              <artifact/ref/null>
  measured_overhead:
    latency_delta:          <value/null>
    throughput_delta:       <value/null>
    resource_delta:         <object/null>
  perturbation_nonclaims:
    - <what the observation cannot establish>
```

If `execution_interference` is `NOT_MEASURED` or `INCONCLUSIVE`, a claim that the observation faithfully represents uninstrumented deployment MUST NOT be emitted.

## 9. Recommended mitigations for observer/probe effects

1. Prefer out-of-band or asynchronous observation when it preserves required facts.
2. Keep evidence writing off the decision-critical path where possible.
3. Separate observer authority from the governed component.
4. Use append-only or independently protected evidence sinks.
5. Pin observer/version/configuration as part of evidence provenance.
6. Quantify instrumentation overhead against an uninstrumented or lower-intrusion baseline.
7. Run paired or randomized A/B measurements where perturbation may change timing-sensitive behavior.
8. Preserve sampling/loss metadata and never infer completeness from absence.
9. For AI evaluations, vary or blind evaluation cues and compare monitored vs deployment-like conditions.
10. Treat observer visibility to the model as a material condition of the evaluation.
11. Where the observer is also an intervention, record pre-intervention state, intervention, and post-intervention observation separately.
12. If perturbation cannot be bounded, downgrade the claim; do not "correct" the data heuristically into a stronger claim.

## 10. Conformance

A CPP conformance runner SHOULD emit one result per requirement:

`PASS | FAIL | NOT_MEASURED | INCONCLUSIVE | ERROR | NOT_APPLICABLE`

A pipeline is CPP-conformant only when every applicable MUST/MUST NOT requirement is `PASS` or justified `NOT_APPLICABLE`.

The conformance verdict is a verdict about **claim-preservation behavior**, not about whether the underlying AI system is safe, correct, aligned, or compliant.

## 11. Non-claims

CPP does not claim:
- that the underlying evidence is factually true merely because its claim is preserved;
- that observer effects can always be eliminated;
- that one scalar assurance score can safely summarize all claim dimensions;
- that an instrumented evaluation necessarily predicts uninstrumented deployment;
- that cryptographic integrity establishes semantic correctness;
- that provenance establishes causality.

## 12. Relationship to Phionyx work

CPP generalizes four previously separate Phionyx ideas into one downstream evidence discipline:

- AIREP: explicit claim scope and `does_not_cover`;
- Measurement Axioms: non-execution/uncertainty/error must not collapse into positive assurance;
- CDE-12: what a reader can establish from a bounded record set;
- draft-abak / control-delivery work: structural result, claim support, and intermediary semantic preservation remain separate.

CPP is proposed here as a separate experimental profile. It should not retroactively change those specifications without their own versioned processes.

CPP is not an AIREP profile at this stage and does not alter AIREP conformance. CPP does not modify Measurement Axioms v1.0 or CDE-12. Reference to draft-abak is descriptive only: CPP is not IETF work and implies no IETF review, adoption, or endorsement.
