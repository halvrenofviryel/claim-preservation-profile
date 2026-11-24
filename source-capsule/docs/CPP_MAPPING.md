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

## Requirement-by-requirement gap inventory

This inventory applies only to the current source-capsule candidate. The labels
describe implementation coverage; they are not CPP conformance verdicts.

- `PARTIAL` means a narrow implemented mechanism addresses part of the
  requirement, while material cases or the general transformation obligation
  remain unimplemented.
- `NOT_IMPLEMENTED` means this module does not evaluate or enforce the
  requirement.
- `NOT_APPLICABLE` would require a justified transformation boundary. No
  requirement is marked that way here because this module has not yet produced a
  CPP transformation result to which such a justification could be attached.

| Requirement | Coverage | Exact implemented boundary or gap |
|---|---|---|
| CPP-1 No silent strengthening | `NOT_IMPLEMENTED` | The module records one declared claim and one finding; it does not construct or compare an input/output claim pair or identify a strengthened dimension. |
| CPP-2 Scope monotonicity | `NOT_IMPLEMENTED` | `scope` is retained from the host profile, but no population, temporal, boundary, or target-scope relation is evaluated. |
| CPP-3 Qualifier preservation | `NOT_IMPLEMENTED` | Generated assessment qualifications stay in the capsule; the module does not prove that source or downstream claim qualifiers were preserved or discharged. |
| CPP-4 Non-claim preservation | `NOT_IMPLEMENTED` | No typed input/output non-claim set or discharge mechanism is implemented. |
| CPP-5 Unknown/non-success preservation | `PARTIAL` | The implemented adapters keep `NOT_MEASURED`, `INCONCLUSIVE`, processing `ERROR`, and revision `UNKNOWN`/`STALE` distinct. Withheld states and unresolved external references are outside the current mappings. |
| CPP-6 Provenance continuity | `PARTIAL` | The record binds a claim ID, subject and contract revisions, adapter version, source reference/digest, selection, and mapping loss. It does not retain a CPP input-claim graph, transformer authority, or inherited/additional evidence chain. |
| CPP-7 Evidence resolvability honesty | `PARTIAL` | `SOURCE_DERIVED` requires supplied bytes and rederivation; `CAPSULE_ONLY` is labeled separately. The module does not resolve or authenticate arbitrary external evidence references. |
| CPP-8 Integrity is not truth | `PARTIAL` | Hash and capsule checks never produce a semantic-truth verdict, and the qualifications state that limit. The module does not evaluate downstream transformations that may misstate integrity as truth. |
| CPP-9 Observation is not effect | `PARTIAL` | Two host-owned agent-claim contracts derive narrow findings from explicit structured receipt/execution or selected effect-observer fields. There is no general delivery/receipt/enforcement/effect relation evaluator. |
| CPP-10 Self-report is not independence | `PARTIAL` | Agent prose, success badges, scores, provider labels, and error text do not establish the selected agent claim. Observer authority and failure-domain independence are not represented or verified. |
| CPP-11 Aggregation preserves denominators | `PARTIAL` | Narrow Inspect/Promptfoo mappings record selected total, completed, scored, unscored, measured, and processing-error counts. General aggregation, exclusion, withheld, and multi-stage denominator provenance are not implemented. |
| CPP-12 Semantic-state preservation across adapters | `PARTIAL` | Findings, applicability, processing, and declared/admitted/omitted/unavailable mapping-loss entries remain separate for the supported mappings. The module does not establish preservation of source semantics outside those explicit fields. |
| CPP-13 Mutable-basis disclosure | `PARTIAL` | Exact source bytes, adapter version, evaluation-contract revision, and subject revision/applicability are recorded when exposed. Some sources expose no usable subject revision, which remains `UNKNOWN`; broader policy/specification basis tracking is absent. |
| CPP-14 Redaction must not strengthen | `NOT_IMPLEMENTED` | The repository records that public fixtures are reviewed projections, but it has no redaction/summarization transformation evaluator or strength comparison. |
| CPP-15 Observer-effect disclosure | `NOT_IMPLEMENTED` | The capsule has no enforced observer-effect assessment covering instrumentation-induced runtime or semantic perturbation. |
| CPP-16 Observation/intervention separation | `NOT_IMPLEMENTED` | The narrow agent fields separate selected observations, but the schema does not classify an observer as passive or intervening or attribute effects caused by intervention. |
| CPP-17 Evaluation-awareness qualification | `NOT_IMPLEMENTED` | The module neither records evaluation awareness nor supports transfer claims from monitored evaluation to unmonitored deployment. |
| CPP-18 Evidence-sink failure | `PARTIAL` | Missing selected observations and admitted processing errors produce distinct non-success states. The module does not monitor an exporter/logger/verifier sink or prove detection of silent recording loss. |
| CPP-19 Sampling/loss accounting | `PARTIAL` | Supported adapters retain selected population counts and explicit mapping-loss entries. They do not cover dropped spans, queue/backpressure loss, selective retention, or general sampling designs. |
| CPP-20 Result co-exposure | `PARTIAL` | A capsule co-locates the three assessment axes, basis, qualifications, scope, and mapping-loss record; the included static viewer exposes the bounded cases. The module cannot enforce co-exposure in downstream dashboards, exports, or decisions. |

The immediate consequence is deliberately narrow: the module may be described as
implementing selected source-binding and state-preservation mechanisms. It must not
be described as CPP-conformant until an actual transformation result evaluates all
applicable requirements and records justified `NOT_APPLICABLE` cases.

## Separate maturity axes

| Axis | Current state |
|---|---|
| CPP profile/repository | Experimental author proposal; public v0.1.0 release |
| Source-capsule module | Unreleased consolidation candidate based on the reviewed local 0.1.0a4 lineage |
| OAAC integration | `NOT_IMPLEMENTED` |
| Independent reproduction | `NOT_MEASURED` |
| External validation | `NOT_MEASURED` |

These axes must remain separate in any future registry or user interface. A module
working in its own repository does not establish OAAC integration or independent
validation.
