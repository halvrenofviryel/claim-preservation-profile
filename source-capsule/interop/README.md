# Real-tool format probe

These two deterministic inputs can generate current Inspect AI and Promptfoo exports without paid inference or an external model API. They test source-format compatibility, not model quality.

The local reference run used Inspect AI `0.3.291`, Promptfoo `0.126.0`, Python `3.12`, and Node `22.23.2`. Upstream formats can change. Keep generated logs outside the repository until their full contents and metadata have been reviewed.

## Inspect AI

```bash
inspect eval interop/inspect_task.py \
  --log-format=json \
  --log-dir /tmp/claim-commons-inspect-logs \
  --display=none
```

The task registers and invokes a deterministic local ModelAPI named `claim-commons-local/synthetic-echo-v1`; no external model is called. Import the generated JSON with `fixtures/profiles/interop-mean.json`. The expected selected metric is `exact/mean = 0.75`. Inspect exposes the invoked provider/model name in `eval.model`, so the admitted source can bind the recorded subject revision for this probe.

## Promptfoo

```bash
promptfoo eval \
  -c interop/promptfooconfig.yaml \
  -o /tmp/claim-commons-promptfoo.jsonl \
  --no-cache
```

Promptfoo returns exit status `100` because one of four assertions intentionally fails. That failed assertion remains a measured score of zero; it is not a provider-processing failure. The expected selected mean is `0.75`.

The JSONL output used by this adapter does not expose a subject revision. The same declared revision therefore remains `UNKNOWN` for Promptfoo applicability even when the numeric measurement and criterion outcome match the Inspect probe.

## What the comparison establishes

The probe checks whether each version-pinned adapter can derive the same declared numeric result and keep format-specific limits visible. It does not show that the tools evaluated the same real model, that their scoring semantics are generally equivalent, or that another party reproduced the run.

## Agent-claim preservation probe

The second probe uses three deterministic cases:

1. a received STOP followed by continued execution;
2. a reported message send with no selected outbox effect; and
3. a reported send for which the selected effect observer is unavailable.

Run it with installed `inspect` and `promptfoo` commands:

```bash
interop/run_agent_assurance.sh /tmp/claim-commons-agent-assurance
```

The reference run used Inspect AI `0.3.291`, Promptfoo `0.126.0`, Python `3.12`, and Node `22.23.2`. Inspect exits `0`. Promptfoo exits `100` because the two observed claims are refuted and the missing-observer assertion cannot complete. The runner records both exit codes, projects the raw logs through an explicit public-field allowlist, and builds `report.json` from the normalized outputs.

The expected per-case findings for both adapters are:

| Case | Evidence finding | Inspect processing | Promptfoo processing |
|---|---|---|---|
| `ignored-stop` | `REFUTED` | `COMPLETED` | `COMPLETED` |
| `false-send-claim` | `REFUTED` | `COMPLETED` | `COMPLETED` |
| `missing-effect-observer` | `NOT_MEASURED` | `COMPLETED` | `ERROR` |

The committed files in `fixtures/agent-assurance/` are the reviewed normalized projections, not hand-authored substitutes for the tool outputs. Their admitted fields are sufficient for `SOURCE_DERIVED` verification by this adapter version. Raw logs remain local because stack traces, framework databases, caches, and environment metadata are outside the public fixture contract.

This probe establishes only that the implemented, version-pinned mappings retain the selected structured distinctions for these three synthetic cases. It does not establish an upstream bug, real email delivery, general semantic equivalence, independent observation, or agent safety.

### Quick review without installing the tools

The committed normalized fixtures and generated report can be inspected directly:

```bash
sha256sum \
  fixtures/agent-assurance/inspect.json \
  fixtures/agent-assurance/promptfoo.jsonl \
  results/agent-assurance-report.json

cmp results/agent-assurance-report.json demo/agent-assurance/data/report.json
```

Expected SHA-256 values:

```text
2c0f1f649c73c8ffd60c95830e980fee5431d133cba10ef1f0ce8e924362d24f  fixtures/agent-assurance/inspect.json
a6277ec8a70c1a5557b84e51f0efe4add79b224d6ba9667306eae619f4f112cc  fixtures/agent-assurance/promptfoo.jsonl
7a0dc9daa12b4f439373d0f3229f3b72c73c0db447b62e60704193b22bf2f6e1  results/agent-assurance-report.json
```

This checks only the committed bytes and internal consistency. It is not a tool rerun or independent validation.

### Full reproduction

Install Python 3.12 with `inspect-ai==0.3.291` and Node 22 with `promptfoo==0.126.0`, then run the wrapper shown above. Compare the resulting `normalized/inspect.json`, `normalized/promptfoo.jsonl`, and `report.json` byte-for-byte with the committed files. A useful report is one of: an exact match, a reproducible disagreement, or an ambiguity in the structured observation contract.
