# Claim repository consolidation

`claim-preservation-profile` is the single maintained public repository for
Phionyx claim-preservation work. It owns the claim model, transformation
relations, conformance corpus, validator, source-capsule schema and source
adapters.

The earlier `claim-commons` repository explored a narrower source-admission
problem. Its reviewed 0.1.0a4 candidate is incorporated under
[`source-capsule/`](../source-capsule/) with exact per-file source hashes in the
migration record. It is no longer a separate product line. Frozen experimental
identifiers are retained as provenance.

OAAC is deliberately outside this ownership boundary. OAAC may consume CPP
records to support a public-interest workflow for asking assurance questions,
running or importing tests, reviewing evidence, recording contestation,
rechecking revisions and making human decisions. OAAC does not define a second
claim schema or validator. AIREP remains a separate runtime evidence protocol.

## Status dimensions

The CPP v0.1.0 profile release, the unreleased source-capsule candidate, and a
future OAAC integration have separate status. The module's local controls do not
make OAAC implemented, and neither status establishes independent reproduction or
external validation. The requirement-level gap inventory is maintained in
[`source-capsule/docs/CPP_MAPPING.md`](../source-capsule/docs/CPP_MAPPING.md).
