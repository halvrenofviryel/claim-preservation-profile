# Status — Claim Preservation Profile (CPP)

```yaml
profile_version: "0.1"
repository_release: "0.1.0"
release_date: "2026-09-14"
status: EXPERIMENTAL
normative_status: author proposal
independent_review: NOT_REQUESTED
independent_reproduction: NOT_MEASURED
deployment_evidence: NOT_MEASURED
standardization_status: NONE
conformance_claims: none
```

## What these values mean

| Field | Meaning here |
| --- | --- |
| `profile_version: "0.1"` | Version of the experimental profile semantics in `spec/v0.1/`. |
| `repository_release: "0.1.0"` | Versioned repository release containing the profile, corpus, schemas, validator, tests and documentation. A release identifier is not a maturity claim. |
| `release_date: "2026-09-14"` | Publication date of this repository release. It does not establish review, reproduction, deployment or adoption. |
| `status: EXPERIMENTAL` | The profile is a research artifact. Requirement numbering, field names and the relation vocabulary may change without a compatibility guarantee. |
| `normative_status: author proposal` | The MUST/MUST NOT language in the profile is the author's proposal for what a conforming pipeline would do. No standards body, working group, consortium or review process has adopted it. |
| `independent_review: NOT_REQUESTED` | No independent review has been requested as of this version. This is a record of what has not happened, not a judgement about the profile's quality. |
| `independent_reproduction: NOT_MEASURED` | Nobody outside the authorship has run this corpus or validator and reported results. No reproduction attempt has been made and failed; none has been made at all. |
| `deployment_evidence: NOT_MEASURED` | The profile has not been applied to a production assurance pipeline, and no deployment data exists. |
| `standardization_status: NONE` | Not submitted to, adopted by, or under consideration at any standards organisation. In particular this is not IETF work. |
| `conformance_claims: none` | No system, product, pipeline or specification is claimed to be CPP-conformant, including the author's own. |

`NOT_MEASURED` and `NOT_REQUESTED` are not failures and are not passes. They record
the absence of a measurement, which is the distinction the profile itself exists to
protect.

## The fixture corpus

The conformance fixtures in this repository — twenty original negative cases, two
hardening negatives, and fifteen positive controls — are **author-created research artifacts**.
CPP-16 and CPP-19 now each have a structured negative/positive
near-neighbour pair and a validator check that mechanically separates the pair.
That establishes internal corpus/rule consistency only. Six of the twenty-two
negative cases state their failure only in prose and are reported by the reference
validator as not mechanically decidable.

They are **not independent empirical validation**. They are not drawn from observed
production incidents, not sampled from a third-party corpus, and not reviewed by
anyone outside the authorship. A validator agreeing with them demonstrates
internal consistency between the corpus and the rules, and nothing more.

## What the reference validator's exit code means

The validator's process exit code reports **run validity** — whether the run was
performed and whether the corpus is structurally well formed. It does not report
whether claims were preserved. Claim-preservation verdicts are in the report body.
A zero exit on a corpus containing twenty-two non-preserving cases is the expected
result, and is the point.

## Relationship to other Phionyx work

CPP v0.1 does not modify AIREP, Measurement Axioms v1.0, CDE-12, or the draft-abak
IETF work area, and is not part of any of them. See
[`research/PRIOR_ART_AND_SCOPE.md`](research/PRIOR_ART_AND_SCOPE.md) for the detail.
