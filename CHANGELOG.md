# Changelog

## Unreleased

- Consolidate the useful source-admission work from the earlier Claim Commons
  prototype as the `source-capsule/` CPP module.
- Preserve exact source provenance and frozen experiment identifiers while
  retiring Claim Commons as a separate maintained claim product.
- Define OAAC as a separate consumer workflow that does not own a second claim
  schema or CPP validator.

All notable changes to this repository are recorded here. Dates are UTC.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely.
Versions refer to the Claim Preservation Profile itself, which is EXPERIMENTAL: no
compatibility guarantee applies across 0.x versions.

## 0.1.0 — 2026-09-14

First public **Experimental** release. This release preserves the initial candidate
at `e5961ab2c54a2ade57bd2901131006480ed7b750` and the public-candidate hardening at
`95e5875ec7d24f013d35b2326b6b41df66cf004f` as separate commits in linear history.
It contains twenty normative requirements, twenty-two negative fixtures, fifteen
positive controls, and 104 passing tests. Six natural-language negative fixtures
deliberately remain not mechanically decidable by the reference validator.

### Added

- Pinned-source cross-project audit for AIREP/CDE-12, Measurement Axioms, and the
  published draft-abak-01 text.
- Structured CPP-16 fixtures `CPP-N21`/`CPP-P14` and a validator rule separating
  passive observation from observer intervention.
- Structured CPP-19 fixtures `CPP-N22`/`CPP-P15` and a validator rule separating a
  complete-population claim from explicitly bounded sampling/loss accounting.
- Regression and mutation tests for the two new rules, source pins, attribution
  corrections, CFF parsing, and fail-closed handling of missing structured facts;
  the suite now contains 104 tests.
- Verified author ORCID and the public position-paper URL, publication date, and DOI
  in `CITATION.cff`.

### Changed

- Narrowed cross-project language to the exact versioned statements supported by
  the audited sources and made the individual Internet-Draft status explicit.
- Completed the v0.1.0 CFF release metadata while keeping the separately published
  position paper's DOI and `date-published` value distinct from CPP metadata.
- Removed the single `license-url` field because it represented only the CC BY 4.0
  side of the repository's documented dual-license boundary.
- Updated corpus/status documentation from 20 negative/13 positive fixtures to 22
  negative/15 positive fixtures. CPP-16 and CPP-19 are no longer described as
  unexercised.

### Fixed

- Removed loose requirement attributions while preserving each fixture's
  `AMPLIFIED_UNSUPPORTED` expected relation: CPP-N02 no longer cites CPP-13;
  CPP-N06 no longer cites CPP-20; CPP-N16 no longer cites CPP-6; CPP-N18 no longer
  cites CPP-20.

The versioned release does not change CPP's Experimental author-proposal status or
create evidence of independent review, reproduction, deployment, conformance, or
standards adoption.

### Pre-release provenance — initial candidate e5961ab2

Initial experimental profile. Local candidate; not released, not published, not
tagged at that commit. The statements below record the state of the preserved
baseline and are retained as history; later hardening and release work is described
above.

#### Added in the initial candidate

- **Initial experimental profile** — `spec/v0.1/CLAIM_PRESERVATION_PROFILE.md`,
  from the supplied v0.1 seed bundle: claim model `C = (P, S, Q, N, E, A, V)`, the
  eight-value relation vocabulary, ten independent strength dimensions, and twenty
  normative requirements CPP-1 … CPP-20.
- **20 negative fixtures from the supplied seed corpus** —
  `conformance/negative-fixtures.json`, copied byte-for-byte from
  `negative_fixtures_v0.1.json` with no edit to any case.
- **Observer-effect / probe-effect requirements** — CPP-15 through CPP-19 retained
  in v0.1 rather than deferred, covering runtime perturbation, observation/intervention
  separation, evaluation-awareness qualification, evidence-sink failure, and
  sampling/loss accounting.
- **Claim-preservation result schema** —
  `spec/v0.1/claim-preservation-result.schema.json`. Keeps result dimensions
  separate rather than collapsing to a boolean or a score; requires an observer-effect
  block on every result; forbids a passing relation alongside recorded violations;
  forbids an uninstrumented generalization when perturbation is `NOT_MEASURED` or
  `INCONCLUSIVE`; requires added evidence for `SUPPORTED_STRENGTHENING`.
- **Positive controls** — `conformance/positive-fixtures.json`, thirteen cases
  covering exact preservation, legitimate scope narrowing, qualifier-preserving
  summarization, supported strengthening with identifiable added evidence, a bounded
  signature claim, acknowledgement not promoted to effect, aggregation preserving the
  denominator, an observer-effect-qualified result, adapter state preservation,
  `NOT_MEASURED` surviving aggregation, unfetched evidence not reported as verified,
  evaluation-awareness transfer supported by a blinded arm, and an evidence-sink
  failure surfaced as a non-success state. Eleven are paired with a negative case via
  `near_neighbour_of` / `load_bearing_difference`, and each pair declares in
  `mechanically_separable` whether the reference validator can actually separate it —
  eight can; three cannot, because the paired negative states its failure only in prose.
- **Validator** — `conformance/validate.py`. Offline, deterministic, standard
  library plus `jsonschema`. Separates corpus validation from claim-relation
  evaluation; derives each relation from structured fields independently of the
  relation a fixture declares, then reconciles the two. Process exit reports run and
  corpus validity; claim verdicts are in the report body.
- **Conformance tests** — `tests/`, 93 tests including mutation tests that weaken
  load-bearing validator rules and assert the corresponding detection is lost.
- **Prior-art and scope statement** — `research/PRIOR_ART_AND_SCOPE.md`, recording
  what CPP does not claim to invent, the bounded candidate contribution, the single
  bounded search observation, and the areas where formal novelty remains open.
- **Common fixture schema** — `conformance/fixture.schema.json`, allowing both
  corpora, with backwards-compatible aliases (`violates`, `input_claim`,
  `bad_output_claim`, `input_population`, `adapter_mapping`, and the rest) so the
  seed negative corpus validates unchanged. The original seed schema is retained as
  `conformance/negative-fixture.schema.json`.
- **Status statement** — `STATUS.md`, and a dual-license boundary in `LICENSE` /
  `LICENSE-CODE`.
- **Local candidate integrity manifest** — `spec/v0.1/CHECKSUMS.sha256`.

#### Substantive corrections to the supplied seed profile

Five corrections were made to `CLAIM_PRESERVATION_PROFILE_v0.1.md` when copying it
to `spec/v0.1/CLAIM_PRESERVATION_PROFILE.md`. Every one is listed here; no other
substantive change was made, and no negative fixture was altered. A `diff` against
the seed shows four hunks, not five: corrections 3 and 5 both fall in §12 and are
adjacent enough to merge into one hunk. They are listed separately because they were
made for different reasons and at different times.

1. **§2 Design principle — added `completeness claim` to the enumerated dimensions.**
   The seed sentence read "semantic strength, scope, certainty, causal implication,
   independence claim, or assurance level". §5 lists "Completeness claim" as
   dimension 8, and CPP-11 and CPP-19 are about completeness, so the central
   invariant omitted a dimension the rest of the profile relies on. This is an
   internal-consistency correction; it narrows what a transformation may do.

2. **§7 Observer/probe-effect extension — added an explicit disclaimer that CPP is
   not derived from the Heisenberg uncertainty principle.** The seed said only "not
   as a statement of quantum mechanics". The added paragraph states that any
   resemblance is at most a loose analogy and that the perturbation modelled is
   classical. Narrowing; no requirement changed.

3. **§12 Relationship to Phionyx work — added CDE-12 to the list, and added an
   explicit non-implication paragraph.** The seed listed AIREP, Measurement Axioms
   and draft-abak but not CDE-12, while this repository documents the CDE-12
   relationship. The added paragraph states that CPP is not an AIREP profile and
   does not alter AIREP conformance, does not modify Measurement Axioms v1.0 or
   CDE-12, and that reference to draft-abak implies no IETF review, adoption or
   endorsement. Narrowing.

4. **Header — added `Version: 0.1` and a `Normative status: Author proposal` line.**
   The seed header carried `Status: Experimental technical profile` only. The added
   line states that the profile is not a standard, not adopted, not independently
   reviewed and not independently reproduced. Narrowing.

5. **§12 — changed "three previously separate Phionyx ideas" to "four".** A
   consequence of correction 3: adding the CDE-12 bullet left the sentence above the
   list counting three items over a list of four. Found in the fresh-context review,
   not at the time of the edit. Editorial, but recorded here because correction 3
   would otherwise be listed as complete when it was not.

The pristine seed bytes were preserved outside the repository for comparison. The
seed profile's SHA-256 as supplied was
`70dac89a559f278a69cc2c55c3a4f6fbb0a8075ea72ca03a04834e4d94a8be22`.

#### Defects found in the fresh-context review and fixed before the baseline commit

A fresh-context adversarial review of the assembled repository ran before the initial
commit. It confirmed defects in three areas, all fixed here:

- **Eight paths by which a check could report a claim-preserving outcome for a fact
  it had not examined.** In `conformance/validate.py`: an evidence-sink failure with
  no emitted status at all, and one with an out-of-vocabulary status, both reported
  as preserving; `basis_pinning` judging only the input basis, so replacing a pinned
  basis with `latest` evaluated as `EQUIVALENT` — the profile's own §7.2 failure
  mode; `scope_monotonicity` ignoring a dropped system boundary; `denominator_preservation`
  returning before inspecting the output and never checking that the enumerated
  buckets sum to the declared total; `uninstrumented_generalization` reporting an
  explicitly unmeasured field as `MEASURED` and preserving. In
  `spec/v0.1/claim-preservation-result.schema.json`: a result whose every dimension
  was `NOT_MEASURED` validated as `EQUIVALENT`, and the MUST stating that an
  amplified dimension sinks the overall relation existed only in a description and
  was not enforced. Each is now a regression test.
- **Two tests that established nothing.** The byte-identity test for the seed corpus
  compared the file to itself and is now pinned against the seed bundle's SHA-256;
  the composition mutation test asserted a locally defined mutant against itself and
  now runs the mutant over the six prose-only negatives.
- **Overstated corpus claims.** The near-neighbour count was wrong, "differing in
  exactly one load-bearing fact" was not true of any pair, and two pairs — later
  three — were not mechanically separable at all while being presented as
  demonstrations of discrimination. Pairings now carry `mechanically_separable`, and
  a test enforces that the declaration matches what the validator actually does.
  Three positive controls were added because no positive fixture exercised CPP-7,
  CPP-17 or CPP-18.

The review also found looseness in four of the seed corpus's violation attributions.
Those fixtures are kept unmodified; the finding is recorded in
`research/PRIOR_ART_AND_SCOPE.md` §6 rather than corrected in place.

#### Initial-candidate state at e5961ab2

- No remote, no push, no GitHub repository, no tag, no release, no DOI, no
  publication.
- No ORCID recorded in `CITATION.cff`: none could be verified from local Phionyx
  metadata in this environment, and none was invented.
- No changes to AIREP, Measurement Axioms, CDE-12, draft-abak, `phionyx-research`,
  `resonatus-ontology`, `measurement-axioms`, or any other existing repository.
