# Changelog

## 0.1.0a4

- Add an explicit per-case agent-claim selector for structured `stop_applied` and `message_sent` observation contracts.
- Preserve two refuted claims and one missing-observer result across normalized Inspect AI `0.3.291` and Promptfoo `0.126.0` exports.
- Keep evidence finding, source processing, and revision applicability separate when Promptfoo reports an assertion-processing error for an unobserved effect.
- Bind Promptfoo agent-claim cases to a structured source revision instead of inferring identity from provider labels.
- Reject duplicate case selection and ignore model prose, pass badges, scores, and error-message text when deriving the selected agent-claim finding.
- Add deterministic real-tool inputs, reviewed public projections, a generated comparison report, and a dependency-free static viewer.
- Expand the bounded control suite from 24 to 32 tests.

## 0.1.0a3

- Record declared, admitted, omitted, and unavailable fields in a source-rederived mapping-loss section in capsule draft 0.3.
- Distinguish a measured failed Promptfoo assertion from an ungraded provider or processing error.
- Keep partial evidence and processing failure as separate axes when graded and failed rows coexist.
- Reject unsupported Promptfoo aggregates, nonfinite thresholds and metrics, non-object JSONL rows, and missing required selector strings.
- Add deterministic, no-API real-tool probes for Inspect AI and Promptfoo plus one shared claim profile.
- Verify the mapping-loss record against exact source bytes alongside selection, measurement, and subject binding.
- Document the bounded local compatibility result and remaining lack of independent reproduction.

## 0.1.0a2

- Rederive selection, measurement, and subject binding from supplied source bytes during source-backed verification.
- Reject Inspect source/profile revision mismatches using the source `eval.model` field.
- Separate evidence finding, applicability, and processing axes in capsule draft 0.2.
- Label source-backed and capsule-only verification levels explicitly.
- Strengthen Inspect population completeness and add adversarial rehash controls.

## 0.1.0a1

- Added the draft 0.1 claim capsule, schema, builder, and verifier.
- Added narrow Inspect AI v2 and Promptfoo JSONL importers.
- Added synthetic complete, partial, unmeasured, and error fixtures.
- Added eight automated controls and CI.
- Documented current evidence, nonclaims, threat boundary, and related work.
