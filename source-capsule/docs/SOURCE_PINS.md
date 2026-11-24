# Source documentation pins

The first two adapters were shaped from public upstream documentation and source at the following revisions, observed on 22 November 2026.

## Inspect AI

- Repository: https://github.com/UKGovernmentBEIS/inspect_ai
- Main revision: `da25f0bf0ad0bd4a6efddb6065ffd33a38da3538`
- Evaluation logs: https://inspect.aisi.org.uk/eval-logs.html

The adapter uses only run `status`, `eval.model`, `results.total_samples`, `results.completed_samples`, selected `scores`, scored and unscored counts, and a selected metric value. In this prototype, `eval.model` is treated as the source-reported subject revision and must equal the profile revision. This narrow equality check does not prove provider identity or semantic equivalence.

The bounded local compatibility probes used the released Python package `inspect-ai==0.3.291` and JSON log version 2. The agent-claim probe admits selected sample metadata and `eval.model`; it does not infer the finding from Inspect's scorer label or aggregate metric.

## Promptfoo

- Repository: https://github.com/promptfoo/promptfoo
- Main revision: `04ab49ccca3242b0309a60919c5c9180dc5b6703`
- Output formats: https://www.promptfoo.dev/docs/configuration/outputs/

The adapter uses only JSONL rows with `gradingResult`, numeric `score`, and an explicit `error` field when present. A scored assertion failure is treated as an observed result; an ungraded error can be a processing failure.

The bounded local numeric compatibility probe used `promptfoo==0.126.0` under Node `22.23.2` with the built-in Echo provider. The agent-claim probe used a deterministic local file provider so structured observation metadata and a source revision could be included explicitly. It treats error presence as source-processing information and never parses error-message text to derive the evidence finding.

These pins identify the material consulted and exact released versions in the local probe. They do not establish compatibility with the full pinned codebase, other configurations, or later revisions.
