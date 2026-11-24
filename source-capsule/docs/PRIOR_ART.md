# Related work and boundaries

CPP Source Capsule is designed to compose with existing work rather than duplicate it.

## Claim Preservation Profile

This directory is a module of [Claim Preservation Profile](../../README.md), not
a separate claim-preservation project. CPP owns the transformation model,
relations, normative requirements, conformance corpus and reference validator.
The source-capsule module adds exact-source binding, narrow source adapters,
mapping-loss records and source rederivation. It does not create a competing
claim model or claim a second project contribution.

## Evaluation frameworks

[Inspect AI](https://inspect.aisi.org.uk/) records evaluation status, results, scores, metrics, samples, and metadata. [Promptfoo](https://www.promptfoo.dev/) runs and compares model evaluations and can export JSON and JSONL results. CPP Source Capsule currently imports only a small documented subset of these formats and does not replace either framework.

## Assurance methods

[Trustworthy and Ethical Assurance](https://www.turing.ac.uk/research/research-projects/trustworthy-and-ethical-assurance-tea) connects claims, arguments, evidence, assumptions, and stakeholder review. A claim capsule is a smaller machine-readable exchange record; it is not a complete assurance case or deliberative process.

## Transparency and signed statements

[RFC 9943](https://www.rfc-editor.org/rfc/rfc9943.html) describes the SCITT architecture for transparent, authentic statements. A digest in this prototype checks exact bytes only. It does not provide issuer identity, authorization, a receipt, or a transparency service.

## Runtime evidence

[AIREP](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol) explores per-decision evidence for AI runtimes. CPP Source Capsule focuses on claim applicability and mapping loss across evaluation records. AIREP is related public research, not a required dependency.

## Claim preservation

The individual Internet-Draft [Claim-Preserving Exchange of AI Evaluation Evidence](https://datatracker.ietf.org/doc/draft-abak-ai-evaluation-claim-preservation/) motivates several distinctions used here. It has no IETF standards status or endorsement. This repository is one experimental mapping path and does not claim conformance to a stable standard.

No project named above has reviewed or endorsed CPP Source Capsule.
