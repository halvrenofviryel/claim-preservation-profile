# Source capsule to CPP mapping boundary

The source-capsule module and the CPP v0.1 result schema have different jobs.
This table prevents the consolidation from being mistaken for conformance that
has not been implemented.

| Source-capsule property | Closest CPP concept | Current relation |
|---|---|---|
| `claim.id`, `claim.text` | input or output claim identity | candidate input; no `C_in -> C_out` pair is constructed |
| `subject.id`, `subject.revision` | basis/revision and scope | partial; subject identity is retained but CPP basis dimensions are broader |
| `source.sha256`, `source.ref` | evidence references and integrity boundary | partial; exact bytes are checked, authority and truth are not |
| `source_binding` | subject/basis applicability | partial; the implemented adapters expose only narrow revision paths |
| `mapping_loss` | transformation provenance, state/qualifier preservation | partial; declared/admitted/omitted/unavailable fields do not decide semantic preservation |
| `measurement` | evidence and assurance-state inputs | partial; preserves selected source state and completeness |
| `assessment.evidence_finding` | claim-support / assurance outcome | partial; does not establish a CPP transformation relation |
| `assessment.applicability` | temporal/basis validity | partial; only the recorded/current revision checks implemented here |
| `assessment.processing` | technical execution state | retained as a separate axis |
| `scope` | scope, qualifications, non-claims | structural placeholder; general semantic coverage is not measured |

## Required before a CPP transformation result can be claimed

1. identify the capsule-backed input claim and the downstream output claim;
2. identify any added evidence and the transformation rule/version;
3. map scope, qualification, non-claim, assurance, causality, independence,
   completeness, freshness, and observer-validity dimensions;
4. run the CPP relation evaluator or report `NOT_MEASURED`/`INCONCLUSIVE` where
   the structured data cannot decide the relation; and
5. retain the source capsule reference and transformation provenance in the CPP
   result.

The consolidation therefore establishes one repository and a clean module
boundary. It does not establish that source capsules are CPP-conformant results,
that their claims are true, or that OAAC is implemented.
