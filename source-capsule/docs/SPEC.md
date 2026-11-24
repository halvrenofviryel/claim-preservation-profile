# Claim capsule draft 0.3

## Purpose

A claim capsule binds one declared claim to one subject revision, one evaluation-contract revision, one admitted source record, one selected measurement, one source-subject binding, and one deterministic criterion. It records processing, evidence finding, and applicability as separate axes so that one cannot replace or mask another.

## Required bindings

- **Claim:** stable identifier and human-readable statement.
- **Subject:** evaluated system identifier and recorded revision.
- **Evaluation contract:** contract identifier, revision, operator, and threshold.
- **Source:** format label, reference, exact-byte SHA-256 digest, and adapter version.
- **Source binding:** whether the source exposes a subject revision, its admitted value, and the source path used by the adapter.
- **Mapping loss:** profile-declared selector/unit fields, selected source paths and transformations, source fields deliberately omitted by the narrow adapter, and required target properties unavailable from the source format.
- **Selection:** every selector field needed to reproduce the narrow adapter mapping.
- **Measurement:** admitted source state, value when present, unit, population completeness, processing completeness, and population counts.
- **Assessment:** separate evidence-finding, applicability, and processing axes, with a basis for each.
- **Scope:** explicit statements of what the record supports and does not support.

## Assessment derivation

The stored assessment has three axes:

1. **Processing** is `ERROR` when the admitted source reports an execution/processing error or a complete observed measurement is malformed. Otherwise it is `COMPLETED` for the implemented mapping. A partial measured population and a processing error can coexist.
2. **Evidence finding** is `NOT_MEASURED` when processing failed or the selected measurement is absent; `INCONCLUSIVE` for a partial or incompletely scored population; and `SUPPORTED` or `REFUTED` after comparing a complete numeric measurement with the declared criterion.
3. **Recorded applicability** is `CURRENT` only when the adapter observed a source revision equal to the declared revision. It is `UNKNOWN` when the source format mapping exposes no subject revision. Construction rejects an observed mismatch rather than emitting a positive capsule for the wrong subject.

Verification derives current applicability separately. A supplied revision different from the recorded revision yields `STALE`; a matching revision yields `CURRENT` only when the source binding is observed and matches; omission of the current revision yields `UNKNOWN`.

These labels are local deterministic results. They do not authenticate the source, validate the evaluation design, or establish semantic truth.

## Source-backed verification

When exact source bytes are supplied, the verifier:

1. checks their SHA-256 digest;
2. requires the exact source format and adapter version implemented by this release;
3. reruns that adapter using the recorded selection;
4. compares the rederived selection, measurement, source binding, and mapping-loss record with the capsule; and
5. recomputes the stored three-axis assessment.

This is labeled `SOURCE_DERIVED`. A rehashed capsule with a fabricated measurement or binding fails if those fields cannot be rederived from the supplied source.

When source bytes are omitted, the verifier checks capsule structure, digest, and internal assessment consistency only. This is labeled `CAPSULE_ONLY`; no source-field claim is made.

## Integrity

The capsule identifier is SHA-256 over canonical JSON bytes of the capsule body without `capsule_id`. The source digest is SHA-256 over exact source bytes. Canonicalization here is the Python `json.dumps` representation with sorted keys, compact separators, UTF-8, and non-finite numbers rejected. This is a prototype convention, not a cross-language canonicalization standard or a signature.

## Mapping-loss boundary

`DECLARED_SELECTED_FIELDS` means the adapter separates profile-declared fields from source-admitted transformations, and records the observed fields or namespaces it deliberately omits. A declared unit is not presented as a source-derived unit. This record is not proof that every semantic dependency in an upstream tool has been discovered. An unavailable target property remains explicit; for example, the current Promptfoo JSONL mapping does not turn `provider.id` into a subject revision.

An assertion failure that has a `gradingResult` and numeric score is a measured outcome, not a processing failure. An error row without an admitted graded result can produce processing `ERROR`. This distinction is adapter behavior and is rechecked from source bytes.

## Structured agent-claim mode

Profiles may select `mode: agent_claim_case` with one exact `case_id`, one `binary_claim` unit, and one of two host-owned observation contracts:

- `stop_applied` requires a structured receipt field and a boolean observation of whether the pending action executed;
- `message_sent` requires an available selected effect observer and numeric before/after values.

The finding is derived only from these admitted structured fields. Agent prose, framework success flags, scalar scores, provider labels, and error-message text do not establish the selected claim. The presence of a source error may set processing to `ERROR`, while an unavailable selected observer keeps the finding `NOT_MEASURED`.

Exactly one source record must match the selected case. Absence yields `NOT_MEASURED`; duplicates are rejected. This prevents a convenient row from silently replacing the intended case, but it does not prove that the host supplied complete or honest observations.

## Change policy

Draft 0.3 is intentionally incompatible with drafts 0.1 and 0.2 because mapping loss is now a required source-derived property. The alpha implementation does not silently upgrade old capsules. A future migration must preserve the original bytes and state which properties could not be derived from the old record.
