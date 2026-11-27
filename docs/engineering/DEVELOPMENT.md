# claim-preservation-profile — development and verification

Active source: `/mnt/data/PHIONYX/repos/claim-preservation-profile`. Edit this independent checkout;
original sources and historical records remain preserved.

## Environment

Python >=3.11; jsonschema >=4.20,<5, pytest/PyYAML dev. Missing jsonschema yields incomplete validation rather than silent success. Source PYTHONPATH includes conformance when importing validate.

## Existing verification entrypoints

```sh
python3 -m pytest tests -q
python3 conformance/validate.py
```

The first command is the bounded starting profile, not a claim of whole-project
qualification. Exact commands, environment, results and unrun gates are registered
in `/mnt/data/PHIONYX/evidence/consolidation/secondary-project-checks.json`.
Each run must retain stdout/stderr, exit code, named cases or machine-readable
results, source revision and dependencies. Distinguish failures, skips and missing
measurements. No external model, paid resource or deployment belongs in a default
offline test. Use fresh temporary state and explicit audit/output directories.

## Maintenance and release boundary

Keep normative spec/checksums and frozen fixture meanings unchanged. Preserve code/prose license split. A valid run can contain adverse claim relations; exit 0 does not imply all source claims preserve strength.

Make issues reproducible with minimal sanitized input, exact version/environment
and expected versus observed behavior. Keep a reviewable change linked to its
issue, contract/compatibility impact and scoped validation. Shared workspace
engineering metadata adds common workflow; it does not override normative tests.

Release only an explicit reviewed source/package allowlist with dependency and
license inventory, changelog, evidence and applicable migration/rollback procedure.
Exclude credentials, customer data, model weights and entire research archives.
Private Git mirroring is not publication, deployment or commercial acceptance.
On this mounted filesystem use the workspace's exact-path Git trust configuration;
never configure wildcard safe.directory or borrow mutable Git object stores.

## Shared runner contract

`engineering/project.json` registers the bounded portable command arrays. From the
workspace root run `python3 tools/workspace.py check claim-preservation-profile --output /tmp/claim-preservation-profile-check-<unique>`; select an isolated interpreter with `--python` when needed.
The output directory must not already exist. Dependencies must be provisioned first;
the runner never installs packages, invokes a model or treats omitted profiles as acceptance.
