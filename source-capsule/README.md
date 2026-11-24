# CPP Source Capsule

CPP Source Capsule is an early research prototype for keeping an AI evaluation claim tied to the measurement, system revision, decision rule, scope, and missing evidence that produced it.

An evaluation result can remain syntactically intact while its meaning becomes stronger during export, import, or presentation. A score can be shown without revealing that only part of the planned population was measured. A successful run can be treated as evidence that a safety claim passed. A past result can remain green after the evaluated system changes.

This CPP module tests one narrow alternative: a deterministic **claim capsule**
that keeps these states visible across two source formats. It is maintained in
the CPP repository rather than as a second claim product.

## What works in this unreleased candidate

- A small, implementation-neutral claim-capsule schema.
- A narrow importer for selected Inspect AI evaluation-log v2 result fields.
- A narrow importer for Promptfoo JSONL rows containing `gradingResult` and numeric `score` fields.
- A dependency-free Python verifier that, when source bytes are supplied, reruns the recorded adapter and compares the rederived selection, measurement, source-subject binding, and mapping-loss record with the capsule.
- Separate evidence-finding (`SUPPORTED`, `REFUTED`, `NOT_MEASURED`, `INCONCLUSIVE`), applicability (`CURRENT`, `STALE`, `UNKNOWN`), and processing (`COMPLETED`, `ERROR`) axes.
- An Inspect mapping that binds `eval.model` to the declared subject revision and rejects mismatches during capsule construction.
- A source-rederived mapping-loss record that distinguishes declared, admitted, omitted, and unavailable fields.
- An explicit per-case agent-claim mode for two host-owned observation contracts: `stop_applied` and `message_sent`. It derives findings from structured observations rather than model prose, framework badges, or error-message text.
- Thirty-two automated controls, including rehashed fabricated-measurement, fabricated-binding, and fabricated-mapping attacks; unknown current revision; unsupported adapter version; scored-population mismatch; contradictory completeness; selector validation; Promptfoo failed-assertion versus processing-error cases; duplicate case selection; and missing-observer preservation.

## What this candidate does not establish

This is a first-party research prototype. In addition to the numeric compatibility probe, the adapters were exercised locally against three deterministic agent-claim cases produced by Inspect AI `0.3.291` and Promptfoo `0.126.0`; the inputs and reproduction steps are in [`interop/`](interop/README.md). Two cases contain counter-evidence to an agent statement. The third has no selected effect observation. The public fixtures are allowlisted projections of actual tool outputs; raw framework logs are not committed because they can contain environment metadata. This was a same-author synthetic compatibility probe, not independent reproduction or evidence about model quality. There are no external users, independent implementations, production deployments, signatures, transparency receipts, or general semantic-truth checks.

`SOURCE_DERIVED` verification means that the capsule digest and deterministic assessment are consistent and that the implemented, version-pinned adapter rederived the same selected fields from the supplied source bytes. `CAPSULE_ONLY` verification checks no source bytes and is labeled separately. Neither level establishes that the claim is true, that the evaluation design is valid, that the source is independent, or that a system is safe.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

Build a capsule from the complete Inspect-shaped fixture:

```bash
cpp-source-capsule import \
  --format inspect-ai-v2 \
  --profile fixtures/profiles/document-triage.json \
  --source fixtures/inspect/complete.json \
  --out capsule.json
```

Verify the capsule and the exact source bytes:

```bash
cpp-source-capsule verify \
  --capsule capsule.json \
  --source fixtures/inspect/complete.json
```

Check applicability against a different current subject revision:

```bash
cpp-source-capsule verify \
  --capsule capsule.json \
  --source fixtures/inspect/complete.json \
  --current-subject-revision model-b
```

The recorded evidence finding and processing result remain visible, while `current_applicability` becomes `STALE`. Omitting the current revision yields `UNKNOWN`; it does not silently reuse the recorded applicability.

The three per-case agent-claim examples and their generated comparison report are under [`fixtures/agent-assurance/`](fixtures/agent-assurance/), [`results/agent-assurance-report.json`](results/agent-assurance-report.json), and [`demo/agent-assurance/`](demo/agent-assurance/). They retain `REFUTED`, `NOT_MEASURED`, `COMPLETED`, `ERROR`, `CURRENT`, and `STALE` as distinct observations. They do not execute a real email service or establish that every relevant effect was observed.

## Role inside CPP

CPP Source Capsule is an import and verification module inside Claim Preservation
Profile. CPP defines the broader transformation-preservation obligations; this
module binds selected source fields and known mapping losses to a portable record.
It does not replace an evaluation framework, assurance case, runtime evidence
format, or transparency service.

- [Inspect AI](https://inspect.aisi.org.uk/) and [Promptfoo](https://www.promptfoo.dev/) run evaluations and preserve their own detailed records.
- [Trustworthy and Ethical Assurance](https://www.turing.ac.uk/research/research-projects/trustworthy-and-ethical-assurance-tea) structures claims, evidence, assumptions, and stakeholder review.
- [SCITT](https://www.rfc-editor.org/rfc/rfc9943.html) defines architecture for transparent, authentic statements.
- [AIREP](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol) explores per-decision runtime evidence.
- The individual Internet-Draft [Claim-Preserving Exchange of AI Evaluation Evidence](https://datatracker.ietf.org/doc/draft-abak-ai-evaluation-claim-preservation/) describes format-neutral preservation requirements. It is an individual draft, not an IETF standard or endorsement.

The research question here is narrower: can a small exchange record preserve an evaluation claim's selected measurement, rule, population completeness, revision applicability, and known limits across tool boundaries without turning missing evidence into support?

OAAC may later consume this module as one input to a public-interest assurance
workflow. OAAC is not implemented by this repository. OAAC must not define a
second claim schema or CPP validator, and this prototype does not establish that
the broader OAAC direction is usable or effective.

## Status and participation

The current answer is **not established** beyond the included fixtures and the
bounded first-party compatibility probe. See [STATUS.md](docs/STATUS.md),
[SPEC.md](docs/SPEC.md), [THREAT_MODEL.md](docs/THREAT_MODEL.md),
[PRIOR_ART.md](docs/PRIOR_ART.md), and the explicit
[source-capsule-to-CPP mapping boundary](docs/CPP_MAPPING.md).

The most useful early contributions are counterexamples, safely shareable export samples, mapping-loss reports, and independent reproductions. Please open an issue before expanding an adapter: narrow, inspectable mappings are preferred to broad format claims.

## License

Code, schema, documentation, and synthetic fixtures are released under the Apache License 2.0. No affiliation or endorsement by the projects cited above is implied.
