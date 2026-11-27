# Threat model

## Assets in scope

- The exact admitted source bytes.
- The selected measurement, population completeness, and processing-completeness fields.
- The declared/admitted/omitted/unavailable mapping-loss record.
- The declared claim, subject revision, criterion, and scope.
- The separation of evidence finding, current applicability, and processing state.

## Failures this prototype can expose

- Source bytes changed after capsule construction.
- Capsule body changed without recomputing its identifier.
- A capsule is rehashed after its selected measurement, source-binding, or mapping-loss fields are fabricated, when the exact source bytes and supported recorded adapter are supplied to the verifier.
- Stored assessment axes or their bases disagree with the deterministic rule encoded in the capsule.
- A known supplied current subject revision differs from the recorded revision.
- A selected measurement is absent, partial, incompletely scored, or explicitly errored in the admitted fields.
- An Inspect source names a model revision different from the profile's declared subject revision.
- A per-case adapter is offered duplicate records for the selected case.
- An agent statement, framework pass badge, scalar score, or error-message phrase conflicts with the structured observation fields used by the selected agent-claim contract. Those presentation fields do not supply the finding.

## Failures outside this prototype

- A dishonest or compromised source that emits internally consistent false data.
- A wrong claim, threshold, evaluator, data set, or sampling design.
- Hidden provider changes that are not observable to the verifier.
- Source-field fabrication by a dishonest producer when the source itself is internally consistent.
- Source-backed rederivation when the source bytes are withheld; this case is explicitly labeled `CAPSULE_ONLY`.
- Incorrect interpretation of upstream fields beyond the implemented mapping.
- Missing, dishonest, incomplete, or non-independent host observations behind a structured field.
- Claims other than the two implemented structured contracts, including recipient delivery, permanent stopping, causal enforcement, and complete mediation.
- Undiscovered semantic dependencies that are not represented by `DECLARED_SELECTED_FIELDS`.
- Collusion, issuer authority, key compromise, unauthorized disclosure, or deletion.
- Semantic equivalence between tools, real-world safety, or production effectiveness.

## Trust boundary

The host supplies the profile, source bytes, adapter selection, and optional current subject revision. A source-backed verifier reruns only the exact adapter versions implemented in this release. The verifier does not allow model-generated text or the evaluated system to approve its own result. The current implementation has no signer identity or authorization model.
