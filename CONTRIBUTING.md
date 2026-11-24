# Contributing to Claim Preservation Profile

CPP is an experimental author proposal. Contributions should make a claim
boundary more inspectable without implying standards adoption, independent
validation, deployment fitness, or semantic truth that has not been measured.

## Useful contributions

- A counterexample where the profile, corpus, validator, source capsule, or
  adapter overstates a result.
- A safely shareable evaluation export together with the exact upstream tool
  and revision that produced it.
- A field-level mapping report that records retained, transformed, omitted, and
  unavailable information.
- An independent implementation or reproduction with its source revision,
  commands, raw outcome, and limitations.
- Accessibility and low-resource usability findings.
- A transformation case that preserves or loses a CPP requirement in a way the
  current corpus does not exercise.

Open an issue before adding a source adapter or changing a normative requirement.
For an adapter proposal, identify the exact source format and revision, fields
admitted, fields omitted, transformation rule, and narrow claim the mapping can
support. New adapters should remain narrow and inspectable rather than claiming
general compatibility with an upstream project.

## Evidence and privacy

Do not submit private evaluation data, credentials, proprietary logs, personal
information, customer material, or raw framework exports that contain local or
environment metadata. Synthetic and projected fixtures must be labeled as such,
and the projection must retain every field used by the asserted result.

A passing test establishes only the tested behavior. It does not by itself
establish compatibility, safety, adoption, interoperability, independence, or
production fitness. Report failed and missing observations separately from
counter-evidence, and do not convert either into a pass.

## License and provenance

Only contribute material that you have the right to submit. State third-party
sources and transformations explicitly. Contributions are accepted under the
license assigned to their repository path in [`LICENSE`](LICENSE): CPP
specification/documentation/fixture material is CC BY 4.0, while executable code
and all material under `source-capsule/` are Apache-2.0. Do not copy code or data
from another project merely because it is publicly accessible.

No project cited by CPP is implied to endorse a contribution or this repository.
