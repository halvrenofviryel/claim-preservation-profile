# Cross-project consistency audit

Audit date: **2026-09-14**
Audit scope: every statement in CPP repository documentation that characterizes
AIREP, Measurement Axioms, CDE-12, or draft-abak, plus the relationship and
non-modification boundaries attached to those statements.

This is a source-consistency audit, not an endorsement, standards determination,
novelty opinion, or conformance assessment. Sources were cloned into a temporary
research directory outside this repository and inspected at the exact commits
below. No source repository was edited.

Temporary audit workspace: `/tmp/cpp-hardening-sources-20260914` (ephemeral and not
part of this repository).

## Frozen source set

| Source | Repository | Branch | Audited commit | Authoritative path used |
| --- | --- | --- | --- | --- |
| AIREP v0.1/v0.2 and CDE-12 v0.2 | `https://github.com/halvrenofviryel/ai-runtime-evidence-protocol` | `main` | `039dbcb22d4b53bb5714877dce65ff15372c49bd` | `spec/airep/v0.1/SPEC.md`; `spec/airep/v0.2/SPEC.md`; `cde12/CDE-12.md` |
| Measurement Axioms v1.0 | `https://github.com/halvrenofviryel/measurement-axioms` | `main` | `ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce` | `spec/v1.0/MEASUREMENT_AXIOMS_SPECIFICATION.md`; `CITATION.cff` |
| draft-abak published revision 01 | `https://github.com/halvrenofviryel/phionyx-research` | `main` | `30e7bcf019b580bf2123955acb256e4894df24a2` | `standards/ietf/agent-control-delivery-evidence/draft/published/01/draft-abak-agent-control-delivery-evidence-01.txt` |

The repository URL, branch, commit, path, section, finding, and correction are part
of each finding below. A branch name alone is not treated as a stable reference;
the commit is the audit basis.

Supplementary interpretation surfaces inspected at the same pins were the AIREP
root `README.md`/`CHANGELOG.md` and v0.1 `STATUS.md`; Measurement Axioms
`README.md`, `CHANGELOG.md`, `THE_MEASUREMENT_AXIOMS.md`, and
`THE_EVIDENCE_STACK.md`; and the draft work-area `README.md`,
`RIGHTS_AND_PROVENANCE.md`, and `reviews/REVIEW_LEDGER.md`. Where candidate text or
work-area commentary differed in authority, the published revision-01 text listed
above controlled the finding.

## Classification vocabulary

- `SUPPORTED` — the frozen source directly supports the statement as written.
- `SUPPORTED_WITH_NARROWING` — the source supports a narrower, version-bounded
  statement; the local wording is narrowed or explicitly bounded here.
- `UNSUPPORTED` — the frozen source does not establish the statement; the statement
  is removed or replaced.
- `NOT_VERIFIED` — the audit could not decide the statement from the frozen sources.

No current statement remains `UNSUPPORTED` or `NOT_VERIFIED`: the three unsupported
baseline formulations listed below were corrected. This does not turn absence of a
conflict into independent validation.

## AIREP findings

### A-01 — explicit scope and `does_not_cover`

- **CPP locations:** `README.md`, “Relationship to existing Phionyx work”;
  `spec/v0.1/CLAIM_PRESERVATION_PROFILE.md`, §12.
- **Classification:** `SUPPORTED`.
- **Source:** `ai-runtime-evidence-protocol` at
  `039dbcb22d4b53bb5714877dce65ff15372c49bd`,
  `spec/airep/v0.1/SPEC.md` §§3 and 5; `spec/airep/v0.2/SPEC.md` §§3 and 9.
- **Finding:** both audited versions define explicit scope with positive coverage
  and `does_not_cover`; v0.1 requires both sides to be populated.
- **Correction:** the CPP text now names v0.1 and v0.2 rather than speaking about an
  unversioned AIREP.

### A-02 — evidence references and resolvability

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit, `spec/airep/v0.1/SPEC.md` §§3–4;
  `spec/airep/v0.2/SPEC.md` §§3–4.
- **Finding:** v0.1 defines typed evidence pointers with `ref` and `resolvable`, and
  says `resolvable: true` is valid only when a verifier can fetch and check the
  artifact; v0.2 retains evidence references and adds content-hash/correlation
  structure.
- **Correction:** the resolvability characterization is attributed specifically to
  v0.1; v0.2 is described only at the level its audited text supports.

### A-03 — integrity does not establish truth

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit, `spec/airep/v0.1/SPEC.md` §§6 and 9.
- **Finding:** v0.1 distinguishes detectable record alteration from correctness of
  the recorded claim and states that a record attests the path, not truth.
- **Correction:** the CPP wording is version-bounded to v0.1; it does not attribute
  a broader philosophical claim to every AIREP version.

### A-04 — stage-specific artifact families and references

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit, `spec/airep/v0.2/SPEC.md` §§2–4.
- **Finding:** v0.2 separates decision, control, execution, and effect artifact
  families, warns that higher assurance does not promote an artifact to another
  stage, and defines cross-artifact correlation/reference fields.
- **Correction:** this statement is expressly attributed to v0.2.

### A-05 — CPP is not an AIREP profile and does not change conformance

- **CPP locations:** `README.md`; profile §12; `STATUS.md`; this document's scope
  statement.
- **Classification:** `SUPPORTED_WITH_NARROWING`.
- **Source:** same repository/commit, `spec/airep/v0.1/SPEC.md` §7 and
  `spec/airep/v0.2/SPEC.md` §5, plus the absence of a CPP profile or CPP reference
  in the pinned tree.
- **Finding:** the audited AIREP versions define their own extension/profile rules
  and do not identify CPP as a profile. A source snapshot cannot prove a timeless
  negative or an organizational decision.
- **Correction:** read the statement as a boundary of this CPP proposal and as an
  observation about the pinned source set, not as a claim about all future AIREP
  versions.

## Measurement Axioms findings

### M-01 — non-success verdicts do not collapse into positive outcomes

- **CPP locations:** `README.md`, relationship and validator paragraphs; profile
  §12.
- **Classification:** `SUPPORTED`.
- **Source:** `measurement-axioms` at
  `ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce`,
  `spec/v1.0/MEASUREMENT_AXIOMS_SPECIFICATION.md` §§3.1–3.3.
- **Finding:** the verdict algebra gives distinct meanings to `PASS`, `FAIL`,
  `NOT_MEASURED`, `INCONCLUSIVE`, `ERROR`, and `NOT_APPLICABLE`; MA-3.4/MA-3.5
  prohibit consumers and aggregates from mapping non-success or unknown values to
  `PASS`.
- **Correction:** “non-execution” was replaced with the exact verdict categories
  the frozen specification defines.

### M-02 — measurement, decision, execution, enforcement, and evidence are separate

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit,
  `spec/v1.0/MEASUREMENT_AXIOMS_SPECIFICATION.md` §§4, 5, and 7.
- **Finding:** the decision record uses orthogonal fields including
  `measurement_status`, `decision_outcome`, and `execution_status`; evidence levels
  and intervention/enforcement states are represented separately. A requested
  intervention is not an applied intervention, and an applied intervention needs a
  material-effect reference.
- **Correction:** local wording enumerates the supported axes instead of describing
  them collectively as “measurement versus non-measurement.”

### M-03 — observer validity/probe effect is not part of frozen v1.0

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED_WITH_NARROWING`.
- **Source:** same repository/commit, complete search of
  `spec/v1.0/MEASUREMENT_AXIOMS_SPECIFICATION.md` and its frozen-v1.0 documentation
  for observer effect, probe effect, perturbation, instrumentation, and
  observer-validity terminology.
- **Finding:** the audited frozen v1.0 source contains no CPP-style
  observer-validity/probe-effect model. Its intervention section is not equivalent
  to CPP's measurement-perturbation model.
- **Correction:** the statement is limited to the pinned frozen v1.0 source; it is
  not a claim about later work or adjacent repositories.

### M-04 — “CPP generalizes Measurement Axioms across transformations”

- **CPP baseline location:** baseline `README.md`, relationship section at
  `e5961ab2c54a2ade57bd2901131006480ed7b750`.
- **Classification:** `UNSUPPORTED`.
- **Source:** same repository/commit and sections as M-01/M-02.
- **Finding:** the sources support shared distinctions, but do not establish that
  CPP is their generalization, their successor, or their combination.
- **Correction:** current text says only that the validator follows the narrower
  shared principle that run validity and positive measurement are different facts.

### M-05 — CPP does not modify Measurement Axioms v1.0

- **CPP locations:** `README.md`; profile §12; `STATUS.md`; prior-art scope.
- **Classification:** `SUPPORTED_WITH_NARROWING`.
- **Source:** the separate repositories and the pinned Measurement Axioms tree at
  `ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce`.
- **Finding:** no CPP edit is present in the audited source snapshot. The statement
  is principally a repository/action boundary, not a proposition established by
  Measurement Axioms itself.
- **Correction:** no compatibility, adoption, or endorsement is inferred.

### M-06 — author ORCID used in `CITATION.cff`

- **CPP location:** `CITATION.cff` (profile author and position-paper author).
- **Classification:** `SUPPORTED`.
- **Source:** `measurement-axioms` at
  `ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce`, `CITATION.cff`, author record.
- **Finding:** the source records Ali Toygar Abak, affiliation Phionyx, with the
  canonical ORCID URL `https://orcid.org/0009-0002-3718-4010`.
- **Correction:** the canonical URL is now present on both author records; no ORCID
  was inferred from a name alone.

## CDE-12 findings

### C-01 — record-focused instrument and bounded reader conclusion

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** `ai-runtime-evidence-protocol` at
  `039dbcb22d4b53bb5714877dce65ff15372c49bd`, `cde12/CDE-12.md` introduction and
  §1.
- **Finding:** CDE-12 says it measures records, not behaviour, and frames its task
  as what a later reader can establish from what a system wrote.
- **Correction:** CPP now calls CDE-12 a record-focused measurement instrument,
  avoiding the broader reading that it measures system truth or safety.

### C-02 — evidence tiers

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit, `cde12/CDE-12.md` §2.
- **Finding:** CDE-12 defines T0–T4 evidence tiers and caps a verdict at the tier
  supporting it.
- **Correction:** none beyond naming CDE-12 v0.2.

### C-03 — `not tested` and `not demonstrated` are distinct

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit, `cde12/CDE-12.md` §3.
- **Finding:** `not demonstrated` records that the rater looked and did not find;
  `not tested` records that the rater did not look or looked too shallowly. The
  source says they are never interchangeable.
- **Correction:** none.

### C-04 — C8–C12 distinctions

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit, `cde12/CDE-12.md` §5, C8–C12.
- **Finding:** C8 requires a delivery acknowledgement at an enforcement point and
  distinct observers; C9 distinguishes applied/refused/no-effect; C10 requires an
  independently observed target-system effect; C11 tests authority separation;
  C12 requires a classified negative record and rejects mere absence as one.
- **Correction:** the local summary names only these supported distinctions and
  does not imply that CDE-12 originated them.

### C-05 — CPP asks whether bounded conclusions remain bounded downstream

- **CPP locations:** `README.md`, relationship section.
- **Classification:** `SUPPORTED_WITH_NARROWING`.
- **Source:** CDE-12 source above for the record-bound premise; CPP profile §§1–3
  for the downstream-transformation question.
- **Finding:** this is a comparison between two separately defined scopes, not a
  claim made by CDE-12 and not a priority claim.
- **Correction:** current wording keeps the two halves separate and says CPP does
  not modify CDE-12.

## draft-abak findings

### D-01 — structural result is separate from claim support

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** `phionyx-research` at
  `30e7bcf019b580bf2123955acb256e4894df24a2`, authoritative published path
  `standards/ietf/agent-control-delivery-evidence/draft/published/01/draft-abak-agent-control-delivery-evidence-01.txt`,
  §§6.5–6.6.
- **Finding:** the draft defines structural aggregate results separately from
  `FULLY_SUPPORTED`, `CONDITIONALLY_SUPPORTED`, and `NOT_SUPPORTED` claim-support
  qualifications; the dimensions are orthogonal.
- **Correction:** current text says the draft “proposes” these distinctions and
  pins revision 01.

### D-02 — co-exposure of structural and support results

- **CPP locations:** profile §12's claim-support characterization; README
  relationship section.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit/path, §6.6.
- **Finding:** where a structural result and a stronger claim are exposed, the
  claim-support qualification is exposed in the same result context.
- **Correction:** this supports comparison with CPP-20 but does not establish that
  CPP is a draft-abak profile.

### D-03 — scope, qualification, and non-claims

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit/path, §5.13.
- **Finding:** the draft requires scope qualifications and non-claims, rejects an
  unqualified structural `PASS`, and limits a signature to properties it binds
  rather than event truth.
- **Correction:** none beyond version/status narrowing.

### D-04 — semantic preservation across intermediaries

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit/path, §5.16 and §8 introduction.
- **Finding:** intermediaries preserve source/transformation information and lost
  distinctions or expose incomplete/ambiguous outcomes; origin preservation alone
  is insufficient for a downstream-reader claim.
- **Correction:** none beyond saying CPP applies a similar question rather than
  claiming formal derivation.

### D-05 — delivery, enforcement, and effect remain distinct

- **CPP locations:** `README.md`, relationship section; profile §12.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit/path, terminology and §§5.5–5.7.
- **Finding:** receiver observation, enforcement outcome, and control-effect
  observation are separately defined and recorded.
- **Correction:** none.

### D-06 — individual Informational Internet-Draft; no consensus implication

- **CPP locations:** `README.md`; profile §12; `STATUS.md`; prior-art relationship
  boundary.
- **Classification:** `SUPPORTED`.
- **Source:** same repository/commit/path, document header, §1.2, and the paragraph
  immediately before §8.
- **Finding:** the document's intended status is Informational, it says its
  requirements do not by themselves define an on-wire protocol, and it expressly
  disclaims treating cited mailing-list discussion as working-group consensus.
- **Correction:** CPP now says “published individual Internet-Draft” and disclaims
  IETF and working-group review, adoption, consensus, and endorsement.

### D-07 — “CPP generalizes draft-abak beyond control delivery”

- **CPP baseline location:** baseline `README.md`, relationship section at
  `e5961ab2c54a2ade57bd2901131006480ed7b750`.
- **Classification:** `UNSUPPORTED`.
- **Source:** same draft source as D-01–D-06.
- **Finding:** the draft establishes its own control-delivery scope. It does not
  establish CPP as a generalization, derivative, successor, or broader standard.
- **Correction:** current wording says CPP “applies a similar preservation
  question” across broader AI assurance transformations.

## Cross-cutting relationship findings

### X-01 — “four previously separate ideas”

- **CPP baseline location:** profile §12 at
  `e5961ab2c54a2ade57bd2901131006480ed7b750`.
- **Classification:** `UNSUPPORTED`.
- **Source:** all three repositories and exact commits in the frozen source table.
- **Finding:** source inspection verifies several compatible distinctions, but not
  that they were “previously separate,” that there are exactly four ideas, or that
  CPP generalizes them into one discipline.
- **Correction:** the profile now says only that CPP “draws on four bodies of prior
  Phionyx work and proposes a separate downstream evidence discipline.”

### X-02 — CPP does not modify or belong to the four source projects

- **CPP locations:** `README.md`; profile §12; `STATUS.md`; prior-art scope;
  `CHANGELOG.md` historical correction 3 and “Not done”; `LICENSE`, dual-licensing
  boundary.
- **Classification:** `SUPPORTED_WITH_NARROWING`.
- **Source:** separate repository identities; pinned trees at
  `039dbcb22d4b53bb5714877dce65ff15372c49bd`,
  `ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce`, and
  `30e7bcf019b580bf2123955acb256e4894df24a2`.
- **Finding:** no CPP integration is present in the audited snapshots, and this
  hardening work changes only the CPP repository. Snapshot inspection cannot prove
  a timeless negative.
- **Correction:** treat the statements as current proposal and repository-action
  boundaries, not as a guarantee about future versioned work.

### X-03 — references create no ownership or endorsement claim

- **CPP locations:** `LICENSE`, dual-licensing boundary; `README.md`, status
  non-claims.
- **Classification:** `SUPPORTED_WITH_NARROWING`.
- **Source:** the separate project identities and pinned trees in the frozen source
  table.
- **Finding:** the audited source snapshots contain no endorsement of CPP. Source
  inspection does not decide every legal ownership question or prove a timeless
  absence of endorsement.
- **Correction:** read the local language as CPP's disclaimer: it claims neither
  ownership nor endorsement. No affirmative property, compatibility, or
  organizational-status claim is inferred.

## Position-paper metadata verification

The public canonical page
`https://huggingface.co/blog/phionyx/access-is-not-yet-verifiability` was inspected
on 2026-09-14. It identifies Ali Toygar Abak / Phionyx as author/publisher, shows a
publication date of 2026-09-13, and links the archived paper DOI
`10.5281/zenodo.22754297`. Those values are recorded on the position-paper
reference in `CITATION.cff`. The DOI belongs to that article; this audit did not
create and does not claim a DOI for CPP.

## Audit result

The surviving current relationship statements are either `SUPPORTED` or
`SUPPORTED_WITH_NARROWING`. Three baseline formulations were `UNSUPPORTED` and have
been replaced: Measurement Axioms as something CPP “generalizes,” draft-abak as
something CPP “generalizes,” and the profile's “four previously separate ideas”
claim. No claim is classified `NOT_VERIFIED` after correction.

The audit found no basis for claiming adoption, endorsement, consensus, derivation,
compatibility, concept priority, exact-phrase priority, or established combination
novelty. It also makes no claim that the referenced projects are correct or that CPP
is conformant with them.

## Fresh-context adversarial review

Performed on 2026-09-14 after assembling the hardening diff and before commit.

| Review focus | Result |
| --- | --- |
| Unsupported novelty claims | Confirmed three unsupported baseline relationship formulations; replaced them and retained explicit phrase/concept/combination/prior-art distinctions. |
| Accidental strengthening of source-project claims | Version-bounded AIREP v0.1/v0.2, Measurement Axioms v1.0, CDE-12 v0.2, and draft-abak-01 statements; no compatibility or derivation claim remains. |
| Record integrity versus truth | CPP-8 and the AIREP v0.1 qualification remain explicit; no integrity-to-truth upgrade found. |
| Observation versus effect | CPP-9 and the CDE-12/draft-abak distinctions remain explicit; no delivery-to-effect upgrade found. |
| Observation versus intervention | Confirmed prior coverage gap; added structured N21/P14 pair, fail-closed rule, direct regression, and rule-removal mutation test. |
| Sampled evidence versus complete population | Confirmed prior coverage gap; added structured N22/P15 pair, exact loss-accounting rule, direct regression, and rule-removal mutation test. |
| Valid run versus positive result | Existing separation remains explicit in README, STATUS, validator output, and tests. |
| Unknown/non-measured state collapse | Existing fail-closed composition tests retained; new malformed/unknown intervention and incomplete sampling cases return non-success states. |
| Observer-effect generalization | Existing CPP-15 uninstrumented-generalization rule and regression retained; no new overclaim found. |
| Accidental IETF/AIREP/Measurement Axioms/CDE-12 membership implication | Current text expressly disclaims membership, adoption, consensus, and endorsement; individual Informational draft status is named. |
