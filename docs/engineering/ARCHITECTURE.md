# claim-preservation-profile — engineering architecture

Source consolidation inspection: 27 November 2026. Existing normative and
historical documents retain their versions; this is a current developer map.

Experimental CPP v0.1 specification/corpus and bounded structured claim-relation validator. Author proposal, not an adopted standard or general semantic oracle.

## Code and ownership

| Surface | Responsibility |
|---|---|
| `spec/v0.1/` | Normative prose/result schema and immutable version checksum. |
| `conformance/validate.py` | Corpus validation separate from structured claim-relation evaluation and run-validity exit status. |
| `conformance/*fixtures.json, tests/` | Negative/positive near-neighbour cases, schema and mutation tests. |
| `research/` | Prior-art/scope and cross-project consistency records. |

## Contract flow

Structured before/after claim fields + explicit added evidence -> dimension-wise relation/checks -> qualified result. Strength is a partial order; incomparable or unmeasured dimensions are not rounded to PASS.

## Implementation and assurance limits

Natural-language entailment is not inferred. Prose-only load-bearing facts produce NOT_MEASURED/INCONCLUSIVE. CPP is related prior art for claim preservation, not a replacement for AIREP or Measurement Axioms.

## Integration and review discipline

GAC–GCA owns its identity, durable cognitive state and learned methods. These
components retain their own domain/evidence ownership; optional model or framework
state never becomes GAC identity by being imported. Treat model proposals and
self-reports as fallible attributed data. Integrity/signatures do not establish
semantic truth, effective enforcement or independent observation.

A reviewer should inspect the named interface, negative controls, dependency
version and actual output before accepting a change. Preserve old failures and
source pins. This guide records inspected implementation; it does not activate
all integrations or establish customer readiness.
